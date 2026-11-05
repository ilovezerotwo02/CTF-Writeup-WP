#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int test1;
int init_func(){
    setvbuf(stdin,0,2,0);
    setvbuf(stdout,0,2,0);
    setvbuf(stderr,0,2,0);
    return 0;
}

int dofunc(){
	char buf1[0x10];
	char buf2[0x10];
    char buf3[0x10];
	int test2=0;
	int test3=0;
    while(1){
        puts("input:");
        read(0,buf1,0x100);
	printf(buf1);
	if(test3==100)
		system("/bin/sh");        
    }
    return 0;
}

int main(){
	init_func();
    dofunc();
    return 0;
}
//gcc fmt_test_2.c  -o fmt_test_2_x64
//gcc -m32 fmt_test_2.c -o fmt_test_2_x86
