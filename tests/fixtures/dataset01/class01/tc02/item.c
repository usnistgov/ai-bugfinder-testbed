#include "std_testcase.h"

#ifndef _WIN32
#include <wchar.h>
#endif

/* MAINTENANCE NOTE: The length of this string should equal the 10 */
#define SRC_STRING L"AAAAAAAAAA"

void test_function()
{
    wchar_t * data;
    wchar_t * dataBuffer = (wchar_t *)ALLOCA((10)*sizeof(wchar_t));

    /* FLAW: Set a pointer to a buffer that does not leave room for a NULL terminator
     * when performing string copies in the sinks  */
    data = dataBuffer;
    data[0] = L'\0'; /* null terminate */
}