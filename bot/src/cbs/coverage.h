// Rule-coverage counters for differential testing: CBS_RULE_HIT marks a situation where an
// unconfirmed rule (tagged RULE? in the code) decides the outcome. Built only into the
// replay_cov tool (CBS_RULE_COVERAGE); a no-op everywhere else.
#pragma once
#include <cstdio>

#ifdef CBS_RULE_COVERAGE
namespace cbs::cov
{
void hit(const char* id);
void dump(std::FILE* f);
} // namespace cbs::cov
#define CBS_RULE_HIT(id) ::cbs::cov::hit(id)
#else
#define CBS_RULE_HIT(id) ((void)0)
#endif
