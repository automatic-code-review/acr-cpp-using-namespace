#include <vector>

using std::vector;

#if defined(Q_OS_WIN)
using company::WindowsOnly;
#elif defined(Q_OS_LINUX)
using company::LinuxOnly;
#endif

int main() {
    return 0;
}
