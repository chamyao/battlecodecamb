#include "cbs/coverage.h"
#ifdef CBS_RULE_COVERAGE
#include <map>
#include <string>

namespace cbs::cov
{
namespace
{
std::map<std::string, long>& counts()
{
	static std::map<std::string, long> m;
	return m;
}
} // namespace
void hit(const char* id) { ++counts()[id]; }
void dump(std::FILE* f)
{
	for (const auto& [k, v] : counts()) std::fprintf(f, "RULEHIT %s %ld\n", k.c_str(), v);
}
} // namespace cbs::cov
#endif
