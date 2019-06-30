#include <iostream>
#include <pjsua-lib/pjsua.h>

int main()
{
    pj_status_t status;
    status = pjsua_create();
    if (status != PJ_SUCCESS) return -1;
    pjsua_destroy();
    return 0;
}
