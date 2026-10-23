// Minimal stackful coroutines: each bot instance runs ordinary C++ on its own stack and
// yields back to the runner at end_turn() or when its fuel runs out (resuming mid-call next
// turn, like a Wasmtime fuel suspension). x86-64 SysV uses a hand-written context switch;
// other platforms fall back to ucontext.
#pragma once
#include <cstddef>
#include <functional>
#include <memory>

namespace cbs
{
class Coroutine
{
public:
	explicit Coroutine(std::size_t stack_size = 256 * 1024);
	~Coroutine();
	Coroutine(const Coroutine&) = delete;
	Coroutine& operator=(const Coroutine&) = delete;

	// Set the body; it runs on the coroutine stack at the next resume(). Exceptions escaping
	// the body are caught and recorded (`crashed()`).
	void start(std::function<void()> body);
	// Run until the body yields or returns. Must not be called from inside the coroutine.
	void resume();
	// Called from inside the body: switch back to the resumer. Throws Cancelled if the
	// coroutine is being cancelled.
	void yield();
	// Unwind a suspended body (destructors run) by making its pending yield() throw.
	void cancel();
	struct Cancelled
	{
	};

	bool done() const { return done_; }
	bool crashed() const { return crashed_; }
	bool running() const { return running_; }

private:
	struct Impl;
	std::unique_ptr<Impl> impl_;
	std::function<void()> body_;
	bool done_ = true, crashed_ = false, running_ = false, cancelling_ = false;
	static void entry(Coroutine* self);
	friend struct CoroAccess;
};
} // namespace cbs
