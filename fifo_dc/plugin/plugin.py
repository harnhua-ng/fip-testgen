def clog2(value):
	base2exp = 0
	num = value - 1
	if(num <= 0):
		PluginUtil.post_error("ERROR  --  Invalid input")
		return 0
	else:
		while(num > 0):
			num = num // 2
			base2exp = base2exp + 1
	return base2exp

def getLoop(depth, val):
	if(depth == 2):
		return 1
	return val

def reduce_depth(depth):
	if(depth == 2):
		return 1
	return 2

def reduce_depth_ret(depth, ret):
	if(depth == 2):
		return 1
	return ret

def check_if_byte_en_required(data_width_a,data_width_b,byte_size):
    if(((data_width_a + data_width_b) > (2 * byte_size)) and ((data_width_a > byte_size) and (data_width_b > byte_size))):
        return 1
    else:
        return 0

def check_byte_enable_width(data_width,bytesize):
    if(data_width > bytesize):
        return 0
    else:
        return 1
	
def cal_addr_depth_range(addr_depth_a,data_width_a,data_width_b):
    min_addr_depth = 2
    max_addr_depth = 65536

    if(data_width_a == data_width_b):
        addr_depth_b = addr_depth_a
    else:
        addr_depth_b = (addr_depth_a * data_width_a) // data_width_b

    if((addr_depth_b > max_addr_depth) or (addr_depth_b < min_addr_depth)):
        return (min_addr_depth,max_addr_depth)
    else:
        return (addr_depth_b,addr_depth_b)

def cal_data_width_range(addr_depth_a,data_width_a,addr_depth_b):
    min_data_width = 1
    max_data_width = 256
    if(addr_depth_a == addr_depth_b):
        data_width_b = data_width_a
    else:
        data_width_b = (addr_depth_a * data_width_a) // addr_depth_b

    if((data_width_b > max_data_width) or (data_width_b < min_data_width)):
        return (min_data_width,max_data_width)
    else:
        return (data_width_b,data_width_b)
		
def get_device_name(value):
	x = runtime_info.device_info.architecture(value)
	return x

def get_tdevice_name(x):
	if(x == "LFD2NX" or x == "LFCPNX" or x == "LFMXO5" or x == "UT24C" or x == "UT24CP"):
		return "LIFCL"
	return x
	
def get_max_bits(family):
	f2 = get_device_name(1)
	if(f2 == "iCE40UP"):
		return (4096 * 30)
	elif(f2 == "LIFCL" or f2 == "LFD2NX" or f2 == "LFMXO5" or f2 == "UT24C" or f2 == "UT24CP"):
		return (18 * 1024 * 84)
	elif(f2 == "LFCPNX"):
		return (18 * 1024 * 204)
	return (2 ** 30)

def check_depth(depth):
	i0 = 1;
	while (i0 < depth):
		i0 = i0*2;
		if(i0 == depth):
			return 1
	PluginUtil.post_error("ERROR -- Depth must be a power of 2 (i.e. 2, 4, 8 ... 16)")
	return 0

def getDepthLimit(family, useFastCtrl):
	if(family == "LIFCL"):
		if(useFastCtrl):
			return 16383
	return 65536

def check_addr_depth_data_width(addr_depth_a,addr_depth_b,data_width_a,data_width_b,family, dir, CtrlType, useFastCtrl):
	result = 1
	max_membits_size = get_max_bits(family)
	min_addr_depth = 1
	max_addr_depth = 65536
	min_data_width = 1
	max_data_width = 256
	if(useFastCtrl):
		max_addr_depth = 16383
	if((addr_depth_a * data_width_a) > max_membits_size):
		result = 0
		PluginUtil.post_error("ERROR  --  Total memory size exceeds the resource limitation! " + str(int(max_membits_size)) + " bits")
	elif((addr_depth_a < min_addr_depth) or (addr_depth_b < min_addr_depth) or (addr_depth_a > max_addr_depth) or (addr_depth_b > max_addr_depth)):
		result = 0
		PluginUtil.post_error("ERROR  --  Address depth is out of range!")
	elif((data_width_a < min_data_width) or (data_width_b < min_data_width) or (data_width_a > max_data_width) or (data_width_b > max_data_width)):
		result = 0
		PluginUtil.post_error("ERROR  --  Data width is out of range!")
	elif((data_width_a > data_width_b) and
		(((data_width_a % data_width_b) != 0) or ((data_width_a // data_width_b) != (1 << clog2((data_width_a // data_width_b)))))):
		result = 0
		PluginUtil.post_error("ERROR  --  Ratio of Data width W / Data width R must be a power of 2 (e.g. 1,2,4)!")
	elif((data_width_b > data_width_a) and
		(((data_width_b % data_width_a) != 0) or ((data_width_b // data_width_a) != (1 << clog2((data_width_b // data_width_a)))))):
		result = 0
		PluginUtil.post_error("ERROR  --  Ratio of Data width R / Data width W must be a power of 2 (e.g. 1,2,4)!")
	elif((addr_depth_a * data_width_a) != (addr_depth_b * data_width_b)):
		result = 0
		PluginUtil.post_error("ERROR  --  (Depth_W x Width_W) and (Depth_R x Width_R) must be equivalent!")
	else:
		if(dir == 'W'):
			if(CtrlType == "FABRIC"):
				result = check_depth(addr_depth_a)
		else:
			if(CtrlType == "FABRIC"):
				result = check_depth(addr_depth_b)
		if(result == 1):
			max_width = data_width_a
			min_width = data_width_b
			if(data_width_b > data_width_a):
				max_width = data_width_b
				min_width = data_width_a
			factor = max_width/min_width
			if(family == "LIFCL"):
				if(factor > 32):
					PluginUtil.post_error("ERROR -- Maximum factor between Width_W and Width_R should be <= 32")
					result = 0
				else:
					result = 1
			elif((family == "LATG1") or (family == "LAV-AT")):
				if(factor > 64):
					PluginUtil.post_error("ERROR -- Maximum factor between Width_W and Width_R should be <= 64")
					result = 0
				else:
					result = 1
			elif(family == "iCE40UP"):
				if(factor > 8):
					PluginUtil.post_error("ERROR -- Maximum factor between Width_W and Width_R should be <= 8")
					result = 0
				else:
					result = 1
			else:
				result = 1
	return result

def check_enable_ecc_valid(data_width_a,data_width_b,byte_en=0,chk_eq_dwid=1):
	result = 0
	if(byte_en):
		result = 0
	elif(chk_eq_dwid):
		result = 1 if((data_width_a == data_width_b) and (data_width_a >= 1 and data_width_a <= 64)) else 0
	else:
		result = 1 if(data_width_a >= 1 and data_width_a <= 64) else 0
	return result

def check_assert_required(ENABLE, TYPE):
	if(ENABLE == "TRUE" or ENABLE == 1):
		if((TYPE == "static-single") or (TYPE == "static-dual")):
			return 1
	return 0

def check_assert_dynamic_required(ENABLE, TYPE):
	if(ENABLE == "TRUE" or ENABLE == 1):
		if((TYPE == "dynamic-single") or (TYPE == "dynamic-dual")):
			return 0
	return 1
	
def check_deassert_required(ENABLE, TYPE):
	if(ENABLE == "TRUE" or ENABLE == 1):
		if(TYPE == "static-dual"):
			return 1
	return 0

def check_deassert_dynamic_required(ENABLE, TYPE):
	if(ENABLE == "TRUE" or ENABLE == 1):
		if(TYPE == "dynamic-dual"):
			return 0
	return 1

def check_mem_implementation(IMPLEMENTATION, WADDR_DEPTH, RADDR_DEPTH, WDATA_WIDTH, RDATA_WIDTH):
	if(IMPLEMENTATION == "LUT"):
		if((WADDR_DEPTH != RADDR_DEPTH) or(WDATA_WIDTH != RDATA_WIDTH)):
			PluginUtil.post_error("ERROR  --  WRITE and READ ADDR_DEPTH and WIDTH must match for LUT implementation")
			return 0
	return 1

def check_flag(ENABLE):
	if(ENABLE == "TRUE" or ENABLE == 1):
		return 0
	return 1

def check_if_full_lvl_valid(ALMOST_FULL_ASSERT_LVL, ALMOST_FULL_DEASSERT_LVL, ENABLE_ALMOST_FULL_FLAG, ALMOST_FULL_ASSERTION,ADDRESS_DEPTH):
	if(ENABLE_ALMOST_FULL_FLAG == "FALSE" or ENABLE_ALMOST_FULL_FLAG == 0):
		return 1
	elif ((ALMOST_FULL_ASSERTION == "dynamic-single") or (ALMOST_FULL_ASSERTION == "dynamic-dual")):
		return 1
	elif (ADDRESS_DEPTH == 2):
		return 1
	elif(ALMOST_FULL_ASSERTION == "static-single"):
		if(ALMOST_FULL_ASSERT_LVL <= ADDRESS_DEPTH):
			return 1
	elif(ALMOST_FULL_ASSERTION == "static-dual"):
		if((ALMOST_FULL_DEASSERT_LVL < ALMOST_FULL_ASSERT_LVL) and (ALMOST_FULL_ASSERT_LVL <= ADDRESS_DEPTH)):
			return 1
	PluginUtil.post_error("ERROR  --  FULL Assert or Deassert LVL is out of range!" + str(int(ADDRESS_DEPTH)))
	return 0

def check_if_empty_lvl_valid(ALMOST_FULL_ASSERT_LVL, ALMOST_FULL_DEASSERT_LVL, ENABLE_ALMOST_FULL_FLAG, ALMOST_FULL_ASSERTION,ADDRESS_DEPTH):
	if(ENABLE_ALMOST_FULL_FLAG == "FALSE" or ENABLE_ALMOST_FULL_FLAG == 0):
		return 1
	elif ((ALMOST_FULL_ASSERTION == "dynamic-single") or (ALMOST_FULL_ASSERTION == "dynamic-dual")):
		return 1
	elif (ADDRESS_DEPTH == 2):
		return 1
	elif(ALMOST_FULL_ASSERTION == "static-single"):
		if(ALMOST_FULL_ASSERT_LVL >= 1):
			return 1
	elif(ALMOST_FULL_ASSERTION == "static-dual"):
		if((ALMOST_FULL_DEASSERT_LVL > ALMOST_FULL_ASSERT_LVL) and (ALMOST_FULL_ASSERT_LVL >= 1)):
			return 1
	PluginUtil.post_error("ERROR  --  EMPTY Assert or Deassert LVL is out of range!")
	return 0
#print check_addr_depth_data_width(0,1,1,1)
