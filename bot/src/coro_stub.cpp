// In the real bot each instance already runs as its own coroutine inside the engine:
// cbs::Coroutine::yield() becomes the engine's end_turn (the instance blocks until its
// next turn). Nothing else of the simulator's coroutine machinery is used.
#include <cambc.h>
#include "cbs/coro.h"

namespace cbs
{
struct Coroutine::Impl
{
};
Coroutine::Coroutine(std::size_t) {}
Coroutine::~Coroutine() = default;
void Coroutine::yield() { cambc::end_turn(); }
void Coroutine::start(std::function<void()>) {}
void Coroutine::resume() {}
void Coroutine::cancel() {}
} // namespace cbs
