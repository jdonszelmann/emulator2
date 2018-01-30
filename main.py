import time


clockspeed = 2000
clockspeed_modifier = 2.0
debug = False
ramsize = 0xff
promsize = 0xff
ram = [0x00]*ramsize
Areg = 0x00
Breg = 0x00
Preg = 0x000
Oreg = 0x00
Ireg = "000"
Jreg = 0x00

labels = {}
callstack = []
popdepth = 0
flags = {"gt":False,"lt":False,"eq":False,"carry":False}

code_memory = [0x000]*promsize


instructions = {"0": lambda x,y: print("0: add (add A + B) \nadding {} + {}".format(Areg,Breg)),
				"1": lambda x,y: print("1: addc (add A + B + C using previous carry out) \nadding {} + {} with carry flag as {}".format(Areg,Breg,flags["carry"])),
				"2": lambda x,y: print("2: sub (add A - B) \nsubtracting {} - {}".format(Areg,Breg)),
				"3": lambda x,y: print("3: subc (subtract A - B - C using previous carry out) \nsubtracting {} - {} with carry flag as {}".format(Areg,Breg,flags["carry"])),
				"4": lambda x,y: print("4: lda (load a ram value into the A register) \nloading {} from ram r{}{}".format(ram[int(x,16)],x,y)),
				"5": lambda x,y: print("5: ldb (load a ram value into the B register) \nloading {} from ram r{}{}".format(ram[int(x,16)],x,y)),
				"6": lambda x,y: print("6: sta (store the value of the A register to a ram location) \nstoring 0x{} to ram r{}{}".format(tohex(Areg,2),x,y)),
				"7": lambda x,y: print("7:"),
				"8": lambda x,y: print("8:"),
				"9": lambda x,y: print("9: jmp (jump to an arbitrary place in the program, based on parameters)"),
				"a": lambda x,y: print("a: imma (load some immediate value into the A register) \nloading 0x{}{} into the A register".format(x,y)),
				"b": lambda x,y: print("b: immb (load some immediate value into the B register) \nloading 0x{}{} into the B register".format(x,y)),
				"c": lambda x,y: print("c: cmp (compare (subtract) A and B but without storing the answer. only the flags are stored)"),
				"d": lambda x,y: print("d: stp (terminate program)"),
				"e": lambda x,y: print("e: out (display a ram value)"),
				"f": lambda x,y: print("f: LDJB (load jump byte, used before a jmp instruction to set the address to the right number)"),
				}

tohex		= lambda x,length	: ("{:0"+str(length)+"x}").format(int(x))
abort		= lambda x 			: [print(x + " \naborting compilation process" ), exit()]
isreg		= lambda x			: x.lower().startswith("r")
regnum		= lambda x			: tohex(int(x[1:]),2) if isreg(x) and int(x[1:]) < ramsize else abort("register name received is not a valid register name ({})".format(x)) 
disasemble	= lambda x			: [instructions[x[0]](x[1],x[2])]
zero		= lambda x			: x if x > 0 else 0

def timeit(func):
	def retfunc(*args,**kwargs):
		t = time.time()
		func()
		if not debug:
			print(time.time()-t, " seconds")
			try:
				print(iterations/(time.time()-t))
			except:
				pass
	return retfunc



def compile_from_asm(file,counterstart=0):
	global code_memory,popdepth

	with open(file) as f:
		lines = f.read()
		lines = [i.strip().replace(" ",",",1).replace(" ","").split(",") for i in lines.split("\n") if i != ""]
		counter = counterstart
		for i in lines:
			cont = False
			for j in range(len(i)):
				if ";" in i[j]:
					i[j] = i[j][:i[j].index(";")]
				if i[j] == "":
					cont = True
			if cont:
				continue
			if i[0].upper() == "LABEL" and len(i) == 2:
				if i[1] in labels:
					abort("redefinition of label {}".format(i[1]))
				labels[i[1]] = counter
				continue
			elif i[0].upper() == "POP" and len(i) == 2:
				counter += 4
				popdepth -= 1
			elif i[0].upper() == "PUSH" and len(i) == 2:
				counter += 4
				popdepth += 1
			elif i[0].upper() == "JMP" and len(i) == 2:
				counter += 1			
			elif i[0].upper() == "JGT" and len(i) == 2:
				counter += 1			
			elif i[0].upper() == "JLT" and len(i) == 2:
				counter += 1			
			elif i[0].upper() == "JEQ" and len(i) == 2:
				counter += 1
			elif i[0].upper() == "JC" and len(i) == 2:
				counter += 1					
			elif i[0].upper() == "MOV" and len(i) == 3:
				counter += 1
			elif i[0].upper() == "ADD" and len(i) == 4:
				counter += 2
			elif i[0].upper() == "ADDC" and len(i) == 4:
				counter += 2				
			elif i[0].upper() == "SUB" and len(i) == 4:
				counter += 2
			elif i[0].upper() == "OUT" and len(i) == 2:
				counter += 1
			elif i[0].upper() == "CALL" and len(i) == 2:
				counter += 2
			elif i[0].upper() == "RET" and len(i) == 1:
				counter += 2
			elif i[0].upper() == "STP" and len(i) == 1:
				counter += 0
			counter += 1
		if popdepth < 0:
			print("warning popdepth negative")
		counter = counterstart
		for i in lines:
			if i[0] == "":
				continue
			code = ""
			if i[0].upper() == "LABEL" and len(i) == 2:
				continue
			elif i[0].upper() == "PUSH" and len(i) == 2:
				if isreg(i[1]):
					code += "4" #lda
					code += regnum(i[1])								
				elif i[1][:2] == "0x":
					code += "a" #imma
					code += i[1][2:]			
				else:
					code += "a" #imma
					code += tohex(i[1],2)
				code_memory[counter] = int(code,16)
				counter += 1
				code = "7fe"
				code_memory[counter] = int(code,16)
				counter += 1
				code = "4fe"
				code_memory[counter] = int(code,16)
				counter += 1
				code = "b01"
				code_memory[counter] = int(code,16)
				counter += 1
				code = "2fe"			
			elif i[0].upper() == "POP" and len(i) == 2:
				code = "8fe"
				code_memory[counter] = int(code,16)
				counter += 1
				code = "4fe"
				code_memory[counter] = int(code,16)
				counter += 1
				code = "b01"
				code_memory[counter] = int(code,16)
				counter += 1
				code = "0fe"
				code_memory[counter] = int(code,16)
				counter += 1
				code = ""
				if isreg(i[1]):
					code += "6" #lda
					code += regnum(i[1])
				else:
					abort("MOV operation requires a register as last argument")	
			
			elif i[0].upper() == "CALL" and len(i) == 2:
				line = tohex(labels[i[1]],3)
				code += "f" # LDBJ
				code += line[0]
				code += line[1]
				code_memory[counter] = int(code,16)
				counter += 1
				code = ""
				code += "9" #jmp
				code += line[2]	
				code += "0"	
				callstack.append(counter + 1)
				
			elif i[0].upper() == "RET" and len(i) == 1:
				line = tohex(callstack.pop(),3)
				code += "f" # LDBJ
				code += line[0]
				code += line[1]
				code_memory[counter] = int(code,16)
				counter += 1
				code = ""
				code += "9" #jmp
				code += line[2]	
				code += "0"	
				callstack.append(counter + 1)
				
			elif i[0].upper() == "JMP" and len(i) == 2:
				line = tohex(labels[i[1]],3)
				code += "f" # LDBJ
				code += line[0]
				code += line[1]
				code_memory[counter] = int(code,16)
				counter += 1
				code = ""
				code += "9" #jmp
				code += line[2]	
				code += "0"		
			elif i[0].upper() == "JC" and len(i) == 2:
				line = tohex(labels[i[1]],3)
				code += "f" # LDBJ
				code += line[0]
				code += line[1]
				code_memory[counter] = int(code,16)
				counter += 1
				code = ""
				code += "9" #jmp
				code += line[2]	
				code += "8"
			elif i[0].upper() == "JGT" and len(i) == 2:
				line = tohex(labels[i[1]],3)
				code += "f" # LDBJ
				code += line[0]
				code += line[1]
				code_memory[counter] = int(code,16)
				counter += 1
				code = ""
				code += "9" #jmp
				code += line[2]	
				code += "2"	
			elif i[0].upper() == "JLT" and len(i) == 2:
				line = tohex(labels[i[1]],3)
				code += "f" # LDBJ
				code += line[0]
				code += line[1]
				code_memory[counter] = int(code,16)
				counter += 1
				code = ""
				code += "9" #jmp
				code += line[2]	
				code += "1"	
			elif i[0].upper() == "JEQ" and len(i) == 2:
				line = tohex(labels[i[1]],3)
				code += "f" # LDBJ
				code += line[0]
				code += line[1]
				code_memory[counter] = int(code,16)
				counter += 1
				code = ""
				code += "9" #jmp
				code += line[2]	
				code += "4"		
			elif i[0].upper() == "MOV" and len(i) == 3:
				if isreg(i[2]):
					if isreg(i[1]):
						code += "4" #lda
						code += regnum(i[1])		
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
						code += "6" #sta
						code += regnum(i[2])						
					elif i[2][:2] == "0x":
						code += "a" #imma
						code += i[1][2:]			
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
						code += "6" #sta
						code += regnum(i[2])
					else:
						code += "a" #imma
						code += tohex(i[1],2)
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
						code += "6" #sta
						code += regnum(i[2])
				else:
					abort("MOV operation requires a register as last argument")
			elif i[0].upper() == "ADDC" and len(i) == 4:
				if isreg(i[3]):
					if isreg(i[1]):
						code += "4" #lda
						code += regnum(i[1])		
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					else:
						code += "a" #imma
						code += tohex(i[1],2)
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					if isreg(i[2]):
						code += "5" #ldb
						code += regnum(i[2])		
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					else:
						code += "b" #immb
						code += tohex(i[2],2)
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					code += "1" #add
					code += regnum(i[3])
				else:
					abort("ADD operation requires a register as last argument")
		
			elif i[0].upper() == "ADD" and len(i) == 4:
				if isreg(i[3]):
					if isreg(i[1]):
						code += "4" #lda
						code += regnum(i[1])		
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					else:
						code += "a" #imma
						code += tohex(i[1],2)
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					if isreg(i[2]):
						code += "5" #ldb
						code += regnum(i[2])		
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					else:
						code += "b" #immb
						code += tohex(i[2],2)
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					code += "0" #add
					code += regnum(i[3])
				else:
					abort("ADD operation requires a register as last argument")
					
			elif i[0].upper() == "OUT" and len(i) == 2:
				if isreg(i[1]):
					code += "4" #lda
					code += regnum(i[1])
				elif i[1][:2] == "0x":
					code += "a" #imma
					code += i[1][2:]	
				else:
					code += "a" #imma
					code += tohex(i[1],2)
				code_memory[counter] = int(code,16)
				counter += 1
				code = "e00" #out
			elif i[0].upper() == "CMP" and len(i) == 3:
				if isreg(i[1]):
					code += "4" #lda
					code += regnum(i[1])		
					code_memory[counter] = int(code,16)
					counter += 1
					code = ""
				else:
					code += "a" #imma
					code += tohex(i[1],2)
					code_memory[counter] = int(code,16)
					counter += 1
					code = ""
				if isreg(i[2]):
					code += "5" #ldb
					code += regnum(i[2])		
					code_memory[counter] = int(code,16)
					counter += 1
					code = ""
				else:
					code += "b" #immb
					code += tohex(i[2],2)
					code_memory[counter] = int(code,16)
					counter += 1
					code = ""
				code = "C00"			


			elif i[0].upper() == "SUB" and len(i) == 4:
				if isreg(i[3]):
					if isreg(i[1]):
						code += "5" #lda
						code += regnum(i[1])		
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					else:
						code += "a" #imma
						code += tohex(i[1],2)
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					if isreg(i[2]):
						code += "6" #ldb
						code += regnum(i[2])		
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					else:
						code += "b" #immb
						code += tohex(i[2],2)
						code_memory[counter] = int(code,16)
						counter += 1
						code = ""
					code += "3" #sub
					code += regnum(i[3])
				else:
					abort("SUB operation requires a register as last argument")
			elif i[0].upper() == "STP" and len(i) == 1:
				code += "d00" #stp
			else:
				abort("SyntaxError incorrect asm syntax ({})".format(i))
				
			code_memory[counter] = int(code,16)
			counter += 1
			if counter >= promsize:
				abort("out of memory")
		

		return counter

@timeit
def execute_bytecode():
	global Areg,Breg,Oreg,Preg,Ireg,Jreg 
	global ram, flags
	
	global iterations
	iterations = 0
	
	while True:
		if clockspeed != -1:
			time.sleep(1/(clockspeed*clockspeed_modifier))
		
		Ireg = tohex(code_memory[Preg],3)
		if Preg >= promsize-1:
			print("end of memory reached")
			break
		if debug:
			print(hex(int(Ireg,16)))
			disasemble(Ireg)

		if Ireg[0] == "0":
			ram[int(Ireg[1] + Ireg[2],16)] = (Areg + Breg) %0xff
			flags["carry"] = Areg+Breg>0xff
		elif Ireg[0] == "1":
			ram[int(Ireg[1] + Ireg[2],16)] = ((Areg + Breg) % 0xff) + int(flags["carry"])
			flags["carry"] = Areg+Breg>0xff
		elif Ireg[0] == "2":
			ram[int(Ireg[1] + Ireg[2],16)] = (Areg - Breg) %0xff
			flags["carry"] = Areg-Breg<0
		elif Ireg[0] == "3":
			pass
		elif Ireg[0] == "4":
			Areg = ram[int(Ireg[1] + Ireg[2],16)]
		elif Ireg[0] == "5":
			Breg = ram[int(Ireg[1] + Ireg[2],16)]
		elif Ireg[0] == "6":
			ram[int(Ireg[1] + Ireg[2],16)] = Areg
		elif Ireg[0] == "7":
			ram[ram[int(Ireg[1] + Ireg[2],16)]] = Areg
		elif Ireg[0] == "8":
			Areg = ram[ram[int(Ireg[1] + Ireg[2],16)]]
		elif Ireg[0] == "9":
			a = str(Jreg) + Ireg[1]
			if int(Ireg[2],16) == int(str(int(flags["carry"]))+str(int(flags["eq"]))+str(int(flags["gt"]))+str(int(flags["lt"])),2):
				Preg = int(a,16) - 1
		elif Ireg[0] == "a":
			Areg = int(Ireg[1] + Ireg[2],16)
		elif Ireg[0] == "b":
			Breg = int(Ireg[1] + Ireg[2],16)
		elif Ireg[0] == "c":
			flags["gt"] 	= Areg > Breg
			flags["lt"] 	= Areg < Breg
			flags["eq"] 	= Areg == Breg
		elif Ireg[0] == "d":
			print("the program has ended itself on instruction #0x{}".format(tohex(Preg,3)))
			break
		elif Ireg[0] == "e":
			print("EMULATOR-->",Areg)
		elif Ireg[0] == "f":
			Jreg = int(Ireg[1] + Ireg[2],16)
		if debug:
			print(ram[:20],Areg,Breg)
			print(Preg)
			for key,item in flags.items():
				print(key,item)
			input("enter to step once...")
			print("______________")
		Preg += 1
		iterations += 1
	print(iterations)

def print_bytecode(stop):
	s = 0
	for i in range(1,stop+1):
		print("0x" + tohex(code_memory[i-1],3), end=" ")
		if i%4==0 and i != 0:
			print("   ",end="")
		if i%16==0 and i != 0:
			print()
			for i in range(s+1,s+16+1):
				print(str(i-1).ljust(6),end="")
				if i%4==0 and i != 0:
					print("   ",end="")
			s += 16
			print()
	print()
	for i in range(s+1,s+16+1):
		print(str(i-1).ljust(6),end="")
		if i%4==0 and i != 0:
			print("   ",end="")
	print()

def print_full_bytecode():
	s = 0
	for i in range(1,promsize):
		print(tohex(code_memory[i-1],3),end="")
		if i%8==0 and i != 0:
			print(" ",end="")
		if i%16==0 and i != 0:
			print()
			for i in range(s+1,s+16+1):
				print(str(i-1).ljust(6),end="")
				if i%4==0 and i != 0:
					print("   ",end="")
			s += 16
			print()
	print()
	for i in range(s+1,s+16+1):
		print(str(i-1).ljust(6),end="")
		if i%4==0 and i != 0:
			print("   ",end="")
	print()
	
# def peephole_optimize(code):
# 	global code_memory
# 	for i in code_memory

	
count = compile_from_asm("stack.asm",0) #HAS TO BE HERE FOR PUSH/POP/CALL TO WORK
count = compile_from_asm("main.asm",count)
# peephole_optimize()
print_bytecode(count)
execute_bytecode()







