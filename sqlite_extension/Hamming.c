// math magic from wikki: http://en.wikipedia.org/wiki/Hamming_weight


#include <stdio.h>
#include <stdlib.h>
//#include <Windows.h> # not sure if required on win TODO: test
#include "sqlite3ext.h"
SQLITE_EXTENSION_INIT1

typedef UINT64 uint64_t;
const uint64_t m1  = 0x5555555555555555; //binary: 0101...
const uint64_t m2  = 0x3333333333333333; //binary: 00110011..
const uint64_t m4  = 0x0f0f0f0f0f0f0f0f; //binary:  4 zeros,  4 ones ...
const uint64_t m8  = 0x00ff00ff00ff00ff; //binary:  8 zeros,  8 ones ...
const uint64_t m16 = 0x0000ffff0000ffff; //binary: 16 zeros, 16 ones ...
const uint64_t m32 = 0x00000000ffffffff; //binary: 32 zeros, 32 ones
const uint64_t hff = 0xffffffffffffffff; //binary: all ones
const uint64_t h01 = 0x0101010101010101; //the sum of 256 to the power of 0,1,2,3...

//This is a naive implementation, shown for comparison,
//and to help in understanding the better functions.
//It uses 24 arithmetic operations (shift, add, and).
static int popcount_1(uint64_t x) {
    x = (x & m1 ) + ((x >>  1) & m1 ); //put count of each  2 bits into those  2 bits
    x = (x & m2 ) + ((x >>  2) & m2 ); //put count of each  4 bits into those  4 bits
    x = (x & m4 ) + ((x >>  4) & m4 ); //put count of each  8 bits into those  8 bits
    x = (x & m8 ) + ((x >>  8) & m8 ); //put count of each 16 bits into those 16 bits
    x = (x & m16) + ((x >> 16) & m16); //put count of each 32 bits into those 32 bits
    x = (x & m32) + ((x >> 32) & m32); //put count of each 64 bits into those 64 bits
    return x;
}

//This uses fewer arithmetic operations than any other known
//implementation on machines with slow multiplication.
//It uses 17 arithmetic operations.
static int popcount_2(uint64_t x) {
    x -= (x >> 1) & m1;             //put count of each 2 bits into those 2 bits
    x = (x & m2) + ((x >> 2) & m2); //put count of each 4 bits into those 4 bits
    x = (x + (x >> 4)) & m4;        //put count of each 8 bits into those 8 bits
    x += x >>  8;  //put count of each 16 bits into their lowest 8 bits
    x += x >> 16;  //put count of each 32 bits into their lowest 8 bits
    x += x >> 32;  //put count of each 64 bits into their lowest 8 bits
    return x & 0x7f;
}

//This uses fewer arithmetic operations than any other known
//implementation on machines with fast multiplication.
//It uses 12 arithmetic operations, one of which is a multiply.
static int popcount_3(uint64_t x) {
    x -= (x >> 1) & m1;             //put count of each 2 bits into those 2 bits
    x = (x & m2) + ((x >> 2) & m2); //put count of each 4 bits into those 4 bits
    x = (x + (x >> 4)) & m4;        //put count of each 8 bits into those 8 bits
    return (x * h01)>>56;  //returns left 8 bits of x + (x<<8) + (x<<16) + (x<<24) + ...
}



static void popcount(sqlite3_context *context,  int argc,  sqlite3_value **argv){
  sqlite3_result_int64(context, popcount_2(sqlite3_value_int(argv[0])) );
}
static void xor(sqlite3_context *context,  int argc,  sqlite3_value **argv){
  sqlite3_result_int64(context, sqlite3_value_int64(argv[0])^sqlite3_value_int64(argv[1]));
}
static void hamming1(sqlite3_context *context,  int argc,  sqlite3_value **argv){
  sqlite3_result_int64(context, popcount_1(sqlite3_value_int64(argv[0])^sqlite3_value_int64(argv[1])));
}
static void hamming2(sqlite3_context *context,  int argc,  sqlite3_value **argv){
  sqlite3_result_int64(context, popcount_2(sqlite3_value_int64(argv[0])^sqlite3_value_int64(argv[1])));
}
static void hamming3(sqlite3_context *context,  int argc,  sqlite3_value **argv){
	uint64_t x = sqlite3_value_int64(argv[0])^sqlite3_value_int64(argv[1]);
	x -= (x >> 1) & m1;             //put count of each 2 bits into those 2 bits
	x = (x & m2) + ((x >> 2) & m2); //put count of each 4 bits into those 4 bits
	x = (x + (x >> 4)) & m4;        //put count of each 8 bits into those 8 bits
	sqlite3_result_int64(context, (x * h01)>>56); //returns left 8 bits of x + (x<<8) + (x<<16) + (x<<24) + ...
}

#ifdef _WIN32
__declspec(dllexport)
#endif

/* SQLite invokes this routine once when it loads the extension.
** Create new functions, collating sequences, and virtual table
** modules here.  This is usually the only exported symbol in
** the shared library.
*/
int sqlite3_extension_init( sqlite3 *db, char **pzErrMsg, const sqlite3_api_routines *pApi){
  SQLITE_EXTENSION_INIT2(pApi)
  int rc = SQLITE_OK;
  sqlite3_create_function(db, "xor", 2, SQLITE_INTEGER, 0, xor, 0, 0);
  sqlite3_create_function(db, "hamming1", 2, SQLITE_INTEGER, 0, hamming1, 0, 0);
  sqlite3_create_function(db, "hamming2", 2, SQLITE_INTEGER, 0, hamming2, 0, 0);
  sqlite3_create_function(db, "hamming3", 2, SQLITE_INTEGER, 0, hamming3, 0, 0);
  sqlite3_create_function(db, "popcount", 1, SQLITE_INTEGER, 0, popcount, 0, 0);
  return rc;
}
// SELECT load_extension('Sqlite3_Hamming.dll');
