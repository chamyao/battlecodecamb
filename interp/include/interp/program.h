// A loaded policy program as plain data: expression and step nodes with spans into pools.
// policy.cpp parses into this form (load_program_codes); the deploy bot can instead embed it
// as constant-initialised arrays (bot/encode_policy.py, load_program_static), so a champion's
// first turn spends no fuel on parsing.
#pragma once
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace interp
{
enum class Op : std::uint16_t; // the block list is in policy.cpp; then const_num, const_bytes, var

// A contiguous run of nodes in one of the program's pools.
template <class T>
struct Span
{
	const T* p = nullptr;
	std::uint32_t n = 0;
	const T& operator[](std::size_t i) const { return p[i]; }
	const T* begin() const { return p; }
	const T* end() const { return p + n; }
	std::size_t size() const { return n; }
};

// No default member initializers: pools are allocated uninitialised and the parser sets every
// field of every node it creates (whole-struct copies cost ~1 fuel per byte in a wasm bot).
struct Expr
{
	Op op;
	int var;
	double num;
	std::string_view bytes;
	Span<Expr> args;
};

struct Step
{
	enum Kind { do_, if_, let_, keep_, end_turn } kind;
	Expr expr; // effect call, condition, or bound value
	int var;
	Span<Step> then, orelse;
};
} // namespace interp
