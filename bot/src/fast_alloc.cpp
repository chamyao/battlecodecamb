// Size-class allocator behind global operator new/delete (bot only; bot/src is not vendored). wasi-libc's malloc/free cost a few
// hundred fuel per pair; the interpreter allocates on most blocks (Value's shared_ptrs and
// vectors) and while loading the policy. Blocks up to kMaxSmall bytes come from per-class
// free lists carved out of 64 KiB slabs (never returned to malloc); larger ones go to malloc.
// Each block carries an 8-byte header with its class (or kLarge) so unsized delete works.
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <new>

namespace
{
constexpr std::size_t kGrain = 16, kMaxSmall = 4096, kClasses = kMaxSmall / kGrain, kHeader = 16, kSlab = 64 * 1024;
constexpr std::uint32_t kLarge = 0xFFFFFFFFu;
void* free_list[kClasses + 1];
char *slab_cur = nullptr, *slab_end = nullptr;

void* alloc(std::size_t n)
{
	if (n == 0) n = 1;
	if (n > kMaxSmall)
	{
		char* p = static_cast<char*>(std::malloc(n + kHeader));
		if (!p) throw std::bad_alloc();
		*reinterpret_cast<std::uint32_t*>(p) = kLarge;
		return p + kHeader;
	}
	const std::size_t c = (n + kGrain - 1) / kGrain; // 1..kClasses
	if (void* p = free_list[c])
	{
		free_list[c] = *static_cast<void**>(p);
		return p;
	}
	const std::size_t sz = c * kGrain + kHeader;
	if (slab_cur + sz > slab_end)
	{
		slab_cur = static_cast<char*>(std::malloc(kSlab));
		if (!slab_cur) throw std::bad_alloc();
		slab_end = slab_cur + kSlab;
	}
	char* p = slab_cur;
	slab_cur += sz;
	*reinterpret_cast<std::uint32_t*>(p) = static_cast<std::uint32_t>(c);
	return p + kHeader;
}

void release(void* q)
{
	if (!q) return;
	char* p = static_cast<char*>(q) - kHeader;
	const std::uint32_t c = *reinterpret_cast<std::uint32_t*>(p);
	if (c == kLarge)
	{
		std::free(p);
		return;
	}
	*static_cast<void**>(q) = free_list[c];
	free_list[c] = q;
}
} // namespace

void* operator new(std::size_t n) { return alloc(n); }
void* operator new[](std::size_t n) { return alloc(n); }
void* operator new(std::size_t n, const std::nothrow_t&) noexcept
{
	try
	{
		return alloc(n);
	}
	catch (...)
	{
		return nullptr;
	}
}
void* operator new[](std::size_t n, const std::nothrow_t& t) noexcept { return operator new(n, t); }
void operator delete(void* p) noexcept { release(p); }
void operator delete[](void* p) noexcept { release(p); }
void operator delete(void* p, std::size_t) noexcept { release(p); }
void operator delete[](void* p, std::size_t) noexcept { release(p); }
void operator delete(void* p, const std::nothrow_t&) noexcept { release(p); }
void operator delete[](void* p, const std::nothrow_t&) noexcept { release(p); }
