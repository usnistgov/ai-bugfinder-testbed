#include "std_testcase.h"
#define SRC_STR "0123456789abcdef0123456789abcde"
typedef struct _charVoid
{
char charFirst[16];
void * voidSecond;
void * voidThird;
} charVoid;
static int staticTrue = 1;
static int staticFalse = 0;
void test_function()
{
if(staticTrue)
{
{
charVoid structCharVoid;
structCharVoid.voidSecond = (void *)SRC_STR;
printLine("code");
}
}
}
