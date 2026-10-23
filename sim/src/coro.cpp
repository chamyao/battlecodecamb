#include "cbs/coro.h"
#include <cstdlib>
#include <cstring>

#if defined(__x86_64__) && !defined(CBS_UCONTEXT)
// switch_stack(void** save_sp, void* load_sp): saves callee-saved registers on the current
// stack, stores the stack pointer to *save_sp, loads load_sp and restores from there.
asm(R"(
	.text
	.globl cbs_switch_stack
	.type cbs_switch_stack,@function
cbs_switch_stack:
	pushq %rbp
	pushq %rbx
	pushq %r12
	pushq %r13
	pushq %r14
	pushq %r15
	subq $8, %rsp
	stmxcsr (%rsp)
	fnstcw 4(%rsp)
	movq %rsp, (%rdi)
	movq %rsi, %rsp
	ldmxcsr (%rsp)
	fldcw 4(%rsp)
	addq $8, %rsp
	popq %r15
	popq %r14
	popq %r13
	popq %r12
	popq %rbx
	popq %rbp
	ret
	.size cbs_switch_stack,.-cbs_switch_stack

	.globl cbs_coro_trampoline
	.type cbs_coro_trampoline,@function
cbs_coro_trampoline:
	andq $-16, %rsp
	movq %r12, %rdi
	callq *%r13
	ud2
	.size cbs_coro_trampoline,.-cbs_coro_trampoline
)");
extern "C" void cbs_switch_stack(void** save_sp, void* load_sp);
extern "C" void cbs_coro_trampoline();

namespace cbs
{
struct Coroutine::Impl
{
	char* stack = nullptr;
	std::size_t size = 0;
	void* coro_sp = nullptr;
	void* caller_sp = nullptr;
};

struct CoroAccess
{
	static void run(Coroutine* c) { Coroutine::entry(c); }
};

void Coroutine::cancel()
{
	if (done_ || running_) return;
	cancelling_ = true;
	resume();
	cancelling_ = false;
	done_ = true;
}

namespace
{
void trampoline_target(Coroutine* c) { CoroAccess::run(c); }
} // namespace

Coroutine::Coroutine(std::size_t stack_size) : impl_(new Impl)
{
	impl_->size = stack_size;
	impl_->stack = static_cast<char*>(std::aligned_alloc(64, stack_size));
}

Coroutine::~Coroutine()
{
	cancel();
	std::free(impl_->stack);
}

void Coroutine::start(std::function<void()> body)
{
	body_ = std::move(body);
	done_ = false;
	crashed_ = false;
	// Initial frame consumed by cbs_switch_stack's restore sequence:
	// [mxcsr/fpucw][r15][r14][r13][r12][rbx][rbp][ret=trampoline], with rsp+8 16-aligned at entry.
	auto top = reinterpret_cast<std::uintptr_t>(impl_->stack + impl_->size);
	top &= ~std::uintptr_t{ 15 };
	auto* sp = reinterpret_cast<std::uint64_t*>(top);
	*--sp = reinterpret_cast<std::uint64_t>(&cbs_coro_trampoline);
	*--sp = 0;																	 // rbp
	*--sp = 0;																	 // rbx
	*--sp = reinterpret_cast<std::uint64_t>(this);								 // r12
	*--sp = reinterpret_cast<std::uint64_t>(&trampoline_target);				 // r13
	*--sp = 0;																	 // r14
	*--sp = 0;																	 // r15
	std::uint32_t mxcsr;
	std::uint16_t fpucw;
	asm volatile("stmxcsr %0" : "=m"(mxcsr));
	asm volatile("fnstcw %0" : "=m"(fpucw));
	*--sp = static_cast<std::uint64_t>(mxcsr) | (static_cast<std::uint64_t>(fpucw) << 32);
	impl_->coro_sp = sp;
}

void Coroutine::resume()
{
	if (done_ || running_) return;
	running_ = true;
	cbs_switch_stack(&impl_->caller_sp, impl_->coro_sp);
	running_ = false;
}

void Coroutine::yield()
{
	cbs_switch_stack(&impl_->coro_sp, impl_->caller_sp);
	if (cancelling_) throw Cancelled{};
}

void Coroutine::entry(Coroutine* self)
{
	try
	{
		self->body_();
	}
	catch (const Cancelled&)
	{
	}
	catch (...)
	{
		self->crashed_ = !self->cancelling_;
	}
	self->done_ = true;
	self->body_ = nullptr;
	cbs_switch_stack(&self->impl_->coro_sp, self->impl_->caller_sp);
	std::abort(); // a finished coroutine is never resumed
}
} // namespace cbs

#else
#include <ucontext.h>

namespace cbs
{
struct Coroutine::Impl
{
	char* stack = nullptr;
	std::size_t size = 0;
	ucontext_t coro{}, caller{};
};

Coroutine::Coroutine(std::size_t stack_size) : impl_(new Impl)
{
	impl_->size = stack_size;
	impl_->stack = static_cast<char*>(std::malloc(stack_size));
}

Coroutine::~Coroutine()
{
	cancel();
	std::free(impl_->stack);
}

static void ucontext_entry(unsigned lo, unsigned hi);

void Coroutine::start(std::function<void()> body)
{
	body_ = std::move(body);
	done_ = false;
	crashed_ = false;
	getcontext(&impl_->coro);
	impl_->coro.uc_stack.ss_sp = impl_->stack;
	impl_->coro.uc_stack.ss_size = impl_->size;
	impl_->coro.uc_link = &impl_->caller;
	const auto p = reinterpret_cast<std::uintptr_t>(this);
	makecontext(&impl_->coro, reinterpret_cast<void (*)()>(&ucontext_entry), 2, static_cast<unsigned>(p), static_cast<unsigned>(p >> 32));
}

struct CoroAccess
{
	static void run(Coroutine* c) { Coroutine::entry(c); }
};

static void ucontext_entry(unsigned lo, unsigned hi)
{
	auto* c = reinterpret_cast<Coroutine*>(static_cast<std::uintptr_t>(lo) | (static_cast<std::uintptr_t>(hi) << 32));
	CoroAccess::run(c);
}

void Coroutine::resume()
{
	if (done_ || running_) return;
	running_ = true;
	swapcontext(&impl_->caller, &impl_->coro);
	running_ = false;
}

void Coroutine::cancel()
{
	if (done_ || running_) return;
	cancelling_ = true;
	resume();
	cancelling_ = false;
	done_ = true;
}

void Coroutine::yield()
{
	swapcontext(&impl_->coro, &impl_->caller);
	if (cancelling_) throw Cancelled{};
}

void Coroutine::entry(Coroutine* self)
{
	try
	{
		self->body_();
	}
	catch (const Cancelled&)
	{
	}
	catch (...)
	{
		self->crashed_ = !self->cancelling_;
	}
	self->done_ = true;
	self->body_ = nullptr;
}
} // namespace cbs
#endif
