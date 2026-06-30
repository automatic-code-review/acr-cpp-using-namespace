#include <vector>

using std::vector;

#ifdef Q_OS_LINUX
using company::LinuxOnly;
#else
using company::Fallback;
#endif

int main() {
    return 0;
}
