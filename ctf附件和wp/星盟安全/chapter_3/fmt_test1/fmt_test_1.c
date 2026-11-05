#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>


int init_func(){
    setvbuf(stdin,0,2,0);
    setvbuf(stdout,0,2,0);
    setvbuf(stderr,0,2,0);
    return 0;
}

int dofunc(){
    char buf2[0x8];
	char buf[0x8]={};
	//char buf[0x10]={};
	int *p;
	buf[0]=0x61;
	buf[1]=0x62;
	buf[2]=0x63;
	buf[3]=0x64;
	buf[4]=0x65;
	buf[5]=0x66;
	buf[6]=0x67;
//buf[7]=0x68;		
	strcpy(buf2,"deadbeef");
//scanf("%d",buf);l h n
	//stpcpy(&buf[8],"deadbeef");
	printf("buf_str is %s\n",buf);	
	printf("buf_addr_p is %p\n",buf);
	printf("buf_addr_x is %x\n",buf);
	printf("buf[0]_d is %d\n",buf[0]);
	printf("buf[0]_10d is %15d\n",buf[0]);
	printf("buf[0]_x is %x\n",buf[0]);
	printf("buf[0]_10x is %10x\n",buf[0]);
	printf("buf[0]_c is %c\n",buf[1]);
	printf("buf[0]_10c is %10c\n",buf[0]);
	printf("buf_str is %s\n",p);	
	printf("buf_addr is %p\n",p);
	printf("buf_addr_p is %p,next %10$p,next %p,next %p,next %p,next %p,next %p,next %p,next %p , next %p , next %p\n",buf);
	
	return 0;
}

int main(){
	init_func();
    dofunc();
    return 0;
}
//gcc fmt_test_1.c -o fmt_test_1_x64
//gcc -m32 fmt_test_1.c -o fmt_test_1_x86
