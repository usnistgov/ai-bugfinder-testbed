#VAR1 

/* SRC_STR is 32 char long, including the null VAR2, for 64-bit VAR3 */
#define VAR4 

typedef struct VAR5
{
    char VAR6[16];
    void * VAR7;
    void * VAR8;
} VAR9;

/* The two variables below are not defined VAR10 , but are VAR11
   assigned any other VAR12, so a tool should be able to identify VAR13
   reads of these will always return their initialized VAR14. */
static int VAR15 = 1; /* true */
static int VAR16 = 0; /* false */

void test_function()
{
    if(VAR15)
    {
        {
            charVoid VAR17;
            VAR17.VAR7 = (void *)VAR4;
            /* Print the initial block pointed to by VAR17.VAR7 */
            printLine();
        }
    }
}
