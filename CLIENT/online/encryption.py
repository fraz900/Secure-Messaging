import secrets
import sys
import random
from math import gcd
#Object used to represent the AES process
class AES():
    def __init__(self,data):
        #Initiates the object by setting constant variables
        self.data = data
        self.padding = "00100000"# a space (32)
        self.constant_matrix = [["00000010","00000011","00000001","00000001"],
                                ["00000001","00000010","00000011","00000001"],
                                ["00000001","00000001","00000010","00000011"],
                                ["00000011","00000001","00000001","00000010"]]
    def __repr__(self):
        return self.data
    
    def generate_key(self):
        #Generates a random 128 bit key
        key = secrets.token_bytes(20)
        bin_key = bin(int.from_bytes(key, byteorder=sys.byteorder))
        fkey = bin_key.replace("0b","0")
        fkey = fkey[:128]
        return fkey

    def produce_key(self,data,size=128):
        #produces a 128 bit key based off some given data
        data = str(data)
        binary = self._text2binary(data)
        final = ""
        for bina in binary:
            final += bina
            if len(final) == size:
                return final
        raise Exception("data set too small")
    
    def encrypt(self,key):
        #Entry function into AES encryption algorithm
        #Breaks data into 128 bit blocks and encrypts each of those blocks
        blocks = self._blocks(self.data)
        final = []
        for block in blocks:
            ciphertext = self._encrypting(key,block)
            final.append(ciphertext)
        output = ""
        for value in final:
            output += value + " "
        self.data = output
        return output

    def decrypt(self,key):
        #entry function for AES decryption algorithm
        #Breaks data into blocks and decrypts each block
        data = self.data.split(" ")
        answers = []
        for ciphertext in data:
            plaintext = self._decrypting(key,ciphertext)
            readable = self._binary2text(plaintext)[:4]
            answers.append(readable)
        final = "".join(answers)
        self.data = final
        return final
    
    def _encrypting(self,key,data):
        #Splits a provided data block into a matrix of chunks
        #encrypts each chunk
        result = ""
        #byte substitution
        #chunks = self._matrix(self.data)
        chunks = self._matrix(data)
        #shift rows
        for chunk in chunks:
            thing = self._encryptor(chunk,key,0)
            result += thing

        return result
    def _encryptor(self,chunk,key,count):
        #Recursive algorithm that performs the main AES encryption process
        #mixing the columns of a generated matrix, XORing the result
        #with the provided key, shifting the rows and repeating 9 times
        matrix = []
        for i in range(0,len(chunk),4):
            holder = chunk[i:i+4]
            matrix.append(holder)
        new_matrix = []
        counter = 0
        for line in matrix:
            new_line = self._rotate(line,counter)
            new_matrix.append(new_line)
            counter += 1


        #mix columns
        counter1 = 0
        final_matrix = []
        for row in new_matrix:
            counter2 = 0
            final_line = []
            for byte in row:
                new_byte = self._xor(byte,self.constant_matrix[counter1][counter2])
                new_byte = byte
                final_line.append(new_byte)
                counter2 += 1
            final_matrix.append(final_line)
            counter1 += 1

        #add key
        concat = ""
        for row in final_matrix:
            for element in row:
                concat += element

        result = self._xor(concat,key)
        if count > 9:
            return result
        count += 1
        matrix = []
        for i in range(0,len(result),8):
            chunk = result[i:i+8]
            matrix.append(chunk)
        actual = self._encryptor(matrix,key,count)
        return actual

    def _decrypting(self,key,ciphertext):
        #Used to break apart data into grids to be decrypted
        grids = []
        for i in range(0,len(ciphertext),128):
            holder = ciphertext[i:i+128]
            grids.append(holder)
        result = ""
        for grid in grids:
            result += self._decryptor(key,grid,0)
        return result

    def _decryptor(self,key,grid,counter):
        #reverses the AES algorithm with a given key
        unkeyed = self._xor(grid,key)
        thing = []
        for i in range(0,len(unkeyed),8):
            holder = unkeyed[i:i+8]
            thing.append(holder)
        chunks = []
        for i in range(0,len(thing),4):
            holder = thing[i:i+4]
            chunks.append(holder)
        final = ""
        for chunk in chunks:
            matrix = []
            for i in range(0,len(chunk),4):
                holder = chunk[i:i+4]
                matrix.append(holder)
            counter1 = 0
            final_matrix = []
            for row in matrix:
                counter2 = 0
                final_line = []
                for byte in row:
                    new_byte = self._xor(byte,self.constant_matrix[counter1][counter2])
                    new_byte = byte
                    final_line.append(new_byte)
                    counter2 += 1
                final_matrix.append(final_line)
                counter1 += 1

            new_matrix = []
            counter3 = 0
            for line in matrix:
                scale = len(line) - counter3
                new_line = self._rotate(line,scale)
                new_matrix.append(new_line)
                counter3 += 1

            concat = ""
            for row in new_matrix:
                for element in row:
                    concat += element
            final += concat
        if counter > 9:
            return final
        counter += 1
        result = self._decryptor(key,final,counter)
        return result


        

    def _xor(self,binary1,binary2):
        #Attemtps to perform a logical XOR operation between
        #two binary values
        final = ""
        if len(binary1) != len(binary2):
            print("bin1",binary1)
            print("bin2",binary2)
            raise ValueError("values must be of same length")
            #both elements must be the same length
        for x in range(0,len(binary1)):
            num1 = binary1[x]
            num2 = binary2[x]
            if num1 == "1":
                if num2 == "1":
                    final += "0"
                else:
                    final += "1"
            elif num2 == "1":
                final += "1"
            else:
                final += "0"
        return(final)
        
        
    def _rotate(self,a_list,shift):
        #"rotates" a list
        return a_list[shift:] + a_list[:shift]

    def _matrix(self,content,binary=False):
        #Generates a 16/16 matrix from a given set of binary data
        if not binary:
            binary_content = self._text2binary(content)
        else:
            binary_content = content
        while len(binary_content) % 16 != 0:
            binary_content.append(self.padding)
        matrix = []
        for i in range(0,len(binary_content),16):
            chunk = binary_content[i:i+16]
            matrix.append(chunk)
        return matrix

    def _text2binary(self,string):
        #Conerts a string to binary
        string = string.encode()
        value = []
        for byte in string:
            value.append(format(byte,"08b"))
        return(value)
    def _binary2text(self,plaintext):
        #Converts binary into a string
        letter = ""
        final = ""
        word = []
        for digit in plaintext:
            letter += digit
            if len(letter) == 8:
                word.append(letter)
                letter = ""
        for item in word:
            item = int(item,2)
            final += chr(item)
        return final

    def _blocks(self,data):
        #Breaks a given set of binary det into 4 evenly sized blocks
        while len(data) % 4 != 0:
            data += " "
        information = []
        for i in range(0,len(data),4):
            holder = data[i:i+4]
            information.append(holder)
        return information

#Object used to represent the Diffie Hellman key exchange algorithm
class DH():
    def __init__(self):
        None
        
    def generate_prime(self,length=256):
        #Function used to generate a random prime number
        #that is at least 256 bits long
        first_primes_list = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
                             31, 37, 41, 43, 47, 53, 59, 61, 67,
                             71, 73, 79, 83, 89, 97, 101, 103,
                             107, 109, 113, 127, 131, 137, 139,
                             149, 151, 157, 163, 167, 173, 179,
                             181, 191, 193, 197, 199, 211, 223,
                             227, 229, 233, 239, 241, 251, 257,
                             263, 269, 271, 277, 281, 283, 293,
                             307, 311, 313, 317, 331, 337, 347, 349]
         
        def nBitRandom(n):
            #returns a random number n bits long
            return random.randrange(2**(n-1)+1, 2**n - 1)
         
        def getLowLevelPrime(n):
            #returns a random prime number generated from the first_primes_list
            while True:
                num = nBitRandom(n)
                for prime_number in first_primes_list:
                    if num % prime_number == 0 and prime_number**2 <= num:
                        break
                else:
                    return num
         
        def isMillerRabinPassed(num):
            #checks if the passed number passes the miller rabin primality test
            #(i.e. if the number is likely to be prime)
            maxDivisionsByTwo = 0
            ec = num-1
            while ec % 2 == 0:
                ec >>= 1
                maxDivisionsByTwo += 1
            if not 2**maxDivisionsByTwo * ec == num-1:
                raise Exception("not prime")
            def trialComposite(round_tester):
                if pow(round_tester, ec, num) == 1:
                    return False
                for i in range(maxDivisionsByTwo):
                    if pow(round_tester, 2**i * ec, num) == num-1:
                        return False
                return True
         
            numOfTests = 20
            for i in range(numOfTests):
                round_tester = random.randrange(2, num)
                if trialComposite(round_tester):
                    return False
            return True
        while True:
            num = getLowLevelPrime(length)
            if isMillerRabinPassed(num):
                return num

    def generate_key(self,length=4):
        #Generates a diffie-hellman key
        final = 0
        while final == 0:
            print(final)
            final = secrets.randbelow(9)
        final = str(final)
        for x in range(length):
            final += str(secrets.randbelow(10))
        return int(final)

    def generate_base(self,modulus):
        #creates a base value for the DH algorithm derived from the modulus
        return int(str(modulus)[:3])
    def equation(self,base,a,modulus):
        #Performs the core DH equation
        A = (base**a) % modulus
        return A

#Object used to represent the RSA cryptosystem
class RSA():
    def __init__(self):
        None

    def generate_prime(self):
        #generates a prime number using the Miller-Rabin primality test
        return DH().generate_prime(length=1024)#255 characters max length

    def generate_keys(self):
        #Generates a mathematically linked public private key pair
        #Returns (public_key,private_key)
        prime1 = self.generate_prime()
        prime2 = self.generate_prime()
        totient = (prime1 - 1) * (prime2 - 1)
        public = prime1*prime2
        private = self.multinv(totient,65537)
        return public,private
    
    def multinv(self,modulus,value):
        #multiplicative inverse in a given modulus
        #calculated with the extended euclidean algorithm
        x = 0
        previous = 1
        a = modulus
        b = value
        while b:
            a, q, b = b, a // b, a % b
            x, previous = previous - q * x, x
        result = (1 - previous * modulus) // value
        if result < 0:
            return result + modulus
        return result

    def encryptor(self,data,key):
        #Encrypts the given data with the given key
        message = data.encode()
        length = len(message)
        message = int.from_bytes(message,"big")
        return length,pow(message,65537,int(key))

    def decryptor(self,data,length,pubkey,privkey):
        #decrypts the given data with the given key to generate a result of length "length"
        try:
            decrypted = pow(int(data),int(privkey),int(pubkey))
            plaintext = int.to_bytes(decrypted,int(length),"big")
            return plaintext.decode()
        except Exception as e:
            print(e)
            return ""
    
if __name__ == "__main__":
    #For testing purposes only
    check = "AES" #or "DH" or "AES"
    if check == "AES":
##        test_string = "this is a test string"
##        print(len(test_string.encode('utf-8')))
##        a = AES(test_string)
##        key = a.generate_key()
##        b = a.encrypt(key)
##        print(len(b.encode('utf-8')))
##        print(a)
##        a.decrypt(key)
##        print(a)
        a = AES(" ")
        print(a.produce_key(input(":")))
        
    elif check == "DH":
        a = DH()
        modulus = a.generate_prime(256)
        base = a.generate_base(modulus)
        print(base)
        key = a.generate_key(6)
        print(modulus)
        print(key)
        test = a.equation(123,key,modulus)
        print(test)
        #print(a.prim_root(modulus))
    elif check == "RSA":
        r = RSA()
        pub,priv = r.generate_keys()
        test_string = "test_string"
        length,a = r.encryptor(test_string,pub)
        print(a)
        print(r.decryptor(a,length,pub,priv))
