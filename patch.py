import sys
import struct
import codecs
from functools import reduce
from PIL import Image

p8 = lambda x: struct.pack("<B", x)
p16 = lambda x: struct.pack("<H", x)
u16 = lambda x: struct.unpack("<H", x)[0]
u32 = lambda x: struct.unpack("<I", x)[0]
ub16 = lambda x: struct.unpack(">H", x)[0]
pb16 = lambda x: struct.pack(">H", x)

data = b""
data_patched = b""
def patch(offset, patch_data):
    global data, data_patched
    if data_patched == b"": data_patched = data
    data_patched = data_patched[:offset] + patch_data + data_patched[offset + len(patch_data):]

def gb_checksum1(data):
    checksum = 0
    for i in range(0x134, 0x14D):
        checksum += (data[i] + 1)
    checksum = 0x100 - (checksum % 0x100)
    return checksum

def gb_checksum2(data):
    checksum = 0
    for i in range(len(data)):
        if i == 0x14E or i == 0x14F: continue
        checksum += data[i]
    checksum %= 0x10000
    return checksum

def decompress_data(arg):
    d = data
    if type(arg) == int:
        offset = arg
    else:
        d = arg
        offset = 0
        
    ptr = offset
    tiles = []
    tile_ptr = ptr + ((d[ptr] & 0b11111100) >> 2) + 2
    cnt = d[ptr] + 1
    ptr += 1
    for c in range(cnt):
        if c % 4 == 0:
            a = d[ptr]
            ptr += 1

        flag = ((a & 0b11000000) >> 6) & 0b11
        a = ((a << 2) + flag) & 0xFF
        if flag == 0:
            tiles.append(b"\x00"*0x10)
        elif flag == 1:
            tiles.append(d[tile_ptr:tile_ptr+0x10])
            tile_ptr += 0x10
        else:
            b = u16(d[tile_ptr:tile_ptr+2])
            tile_ptr += 2
            tile = b""
            for _ in range(0x10):
                if b & 0x8000 == 0:
                    tile += p8(0x00)
                else:
                    tile += p8(d[tile_ptr])
                    tile_ptr += 1
                b <<= 1

            if flag == 3:
                tile += b"\x00"
                for i in range(0x0F):
                    tile = tile[:i+2] + p8(tile[i] ^ tile[i+2]) + tile[i+3:]
            tiles.append(tile[:0x10])
    return tiles, tile_ptr - offset

def compress_data(tiles):
    compressed_data = b""
    compressed_tile = b""
    result_flag = 0

    n_tile = len(tiles) // 0x10
    compressed_data += p8(n_tile - 1)
    for i in range(n_tile):
        flag = 0
        result_tile = b""
        tile = tiles[i*0x10:i*0x10+0x10] + b"\x00"
        if tile[:0x10] != b"\x00"*0x10:
            xor_tile = tile[:2]
            for j in range(0x0F):
                xor_tile += p8(tile[j] ^ tile[j+2])
            xor_tile = xor_tile[:0x10]
            tile = tile[:0x10]

            bit1 = 0
            result_tile1 = b""
            for j in range(len(tile)):
                bit1 <<= 1
                if tile[j] != 0:
                    result_tile1 += p8(tile[j])
                    bit1 |= 1

            bit2 = 0
            result_tile2 = b""
            for j in range(len(xor_tile)):
                bit2 <<= 1
                if xor_tile[j] != 0:
                    result_tile2 += p8(xor_tile[j])
                    bit2 |= 1

            if len(result_tile1) <= len(result_tile2):
                if len(result_tile1) + 2 < 0x10:
                    flag = 2
                    result_tile = p16(bit1) + result_tile1
            else:
                if len(result_tile2) + 2 < 0x10:
                    flag = 3
                    result_tile = p16(bit2) + result_tile2
            
            if flag == 0:
                flag = 1
                result_tile = tile

        result_flag |= flag
        if i % 4 == 3:
            compressed_data += p8(result_flag)
            result_flag = 0
        elif i == n_tile - 1:
            result_flag <<= (2 * (3 - (i % 4)))
            compressed_data += p8(result_flag)

        result_flag <<= 2
        compressed_tile += result_tile

    compressed_data += compressed_tile
    return compressed_data

def get_title(img):
    X = 160
    Y = 144
    img = img.crop( (48, 40, 48+X, 40+Y) )

    pal = dict(map(lambda x: (x[1], x[0]), enumerate(sorted(list(set(img.getdata())), reverse=True))))

    img_2bpp = [ [0]*X for _ in range(Y) ]
    for i in range(Y):
        for j in range(X):
            p = img.getpixel((j, i))
            t = list(map(lambda x: abs(x[0]-p[0]), pal))
            img_2bpp[i][j] = t.index(min(t))

    tile_idx = 1
    tiles_k = {"0"*64: 0}
    tiles = b"\x00"*16
    tilemap = []
    for i in range(Y // 8):
        for j in range(X // 8):
            a = ""
            for k in range(8):
                for l in range(8):
                    a += str(img_2bpp[i*8+k][j*8+l])
            
            if (a in tiles_k) == False:
                tiles_k[a] = tile_idx
                tilemap.append(tile_idx)
                tile_idx += 1

                lb = 0
                hb = 0
                for m in range(len(a)):
                    color = int(a[m])
                    lb |= ((color & 0b10) >> 1) << (7 - (m % 8))
                    hb |= (color & 0b01) << (7 - (m % 8))
                    if m % 8 == 7:
                        tiles += p8(hb) + p8(lb)
                        lb = 0
                        hb = 0
            else:
                tilemap.append(tiles_k[a])

    return tiles, b"".join(map(lambda x: p8((x + 0x80) & 0xFF), tilemap))

def get_sgb_border(img):
    TILE1_X = 64
    TILE1_Y = 192
    TILE1_W = 32
    TILE1_H = 16
    TILE2_X = 96
    TILE2_Y = 192
    TILE2_W = 96
    TILE2_H = 32
    TILE3_X = 136
    TILE3_Y = 184
    TILE3_W = 16
    TILE3_H = 8
    TILE4_X = 160
    TILE4_Y = 184
    TILE4_W = 16
    TILE4_H = 8

    tile1_img = img.crop( (TILE1_X, TILE1_Y, TILE1_X+TILE1_W, TILE1_Y+TILE1_H) )
    tile2_img = img.crop( (TILE2_X, TILE2_Y, TILE2_X+TILE2_W, TILE2_Y+TILE2_H) )
    tile3_img = img.crop( (TILE3_X, TILE3_Y, TILE3_X+TILE3_W, TILE3_Y+TILE3_H) )
    tile4_img = img.crop( (TILE4_X, TILE4_Y, TILE4_X+TILE4_W, TILE4_Y+TILE4_H) )

    tile1_idxs = [ [16, 17, 18, 19], [32, 33, 34, 35] ]
    tile2_idxs = [ [ x for x in range(52, 64) ], [ x for x in range(68, 80) ], [ x for x in range(84, 96) ], [ x for x in range(100, 112) ] ]
    tile3_idxs = [ [41, 42] ]
    tile4_idxs = [ [44, 45] ]
 
    t, _ = decompress_data(0xDF53)
    sgb_border_tiles = [ t[i]+t[i+1] for i in range(0, len(t), 2) ]
    sgb_border_tiles[64] = b"\x00\xFF"*8 + b"\xFF"*16

    const_palette = [14, 4, 3, 2, 15]
    pal = dict([ (color, const_palette[i]) for i, color in enumerate(sorted(list(set(list(tile1_img.getdata()) + list(tile2_img.getdata()))))) ])

    def insert_new_tile(w, h, tile_img, tile_idxs):
        for i in range(h // 8):
            for j in range(w // 8):
                a = ""
                for y in range(8):
                    for x in range(8):
                        p = tile_img.getpixel(((j*8)+x, (i*8)+y))
                        a += hex(pal[p])[2:]
                b1 = 0
                b2 = 0
                b3 = 0
                b4 = 0
                tile1 = b""
                tile2 = b""
                for m in range(len(a)):
                    color = int(a[m], 16)
                    b1 |= (color & 0b0001) << (7 - (m % 8))
                    b2 |= ((color & 0b0010) >> 1) << (7 - (m % 8))
                    b3 |= ((color & 0b0100) >> 2) << (7 - (m % 8))
                    b4 |= ((color & 0b1000) >> 3) << (7 - (m % 8))
                    if m % 8 == 7:
                        tile1 += p8(b1) + p8(b2)
                        tile2 += p8(b3) + p8(b4)
                        b1 = 0
                        b2 = 0
                        b3 = 0
                        b4 = 0
                sgb_border_tiles[tile_idxs[i][j]] = tile1 + tile2

    insert_new_tile(TILE1_W, TILE1_H, tile1_img, tile1_idxs)
    insert_new_tile(TILE2_W, TILE2_H, tile2_img, tile2_idxs)
    insert_new_tile(TILE3_W, TILE3_H, tile3_img, tile3_idxs)
    insert_new_tile(TILE4_W, TILE4_H, tile4_img, tile4_idxs)

    sgb_border_tiles = [ sgb_border_tiles[i // 2][:0x10] if i % 2 == 0 else sgb_border_tiles[i // 2][0x10:] for i in range(len(sgb_border_tiles) * 2) ]
    return b"".join(sgb_border_tiles)

def get_case_title(img, all_tiles=None):
    W = 8 * 8
    H = 8 * 8
    img = img.crop( (48, 56, 48+W, 56+H) )

    pal = dict(map(lambda x: (x[1], x[0]), enumerate(sorted(list(set(img.getdata())), reverse=True))))

    img_2bpp = [ [0]*W for _ in range(H) ]
    for i in range(H):
        for j in range(W):
            p = img.getpixel((j, i))
            t = list(map(lambda x: abs(x[0]-p[0]), pal))
            img_2bpp[i][j] = t.index(min(t))

    tiles_k = {}
    tiles = []
    tilemap = []
    for i in range(H // 8):
        tilemap_w = []
        for j in range(W // 8):
            a = ""
            for k in range(8):
                for l in range(8):
                    a += str(img_2bpp[i*8+k][j*8+l])

            if (a in tiles_k) == False:
                lb = 0
                hb = 0
                tile = b""
                for m in range(len(a)):
                    color = int(a[m])
                    lb |= ((color & 0b10) >> 1) << (7 - (m % 8))
                    hb |= (color & 0b01) << (7 - (m % 8))
                    if m % 8 == 7:
                        tile += p8(hb) + p8(lb)
                        lb = 0
                        hb = 0
                tiles.append(tile)
                tiles_k[a] = tile

                if all_tiles != None:
                    if tile == b"\xFF"*0x10: tilemap_w.append(0x88)
                    else: tilemap_w.append(all_tiles.index(tile))
            else:
                if all_tiles != None:
                    if tile == b"\xFF"*0x10: tilemap_w.append(0x88)
                    else: tilemap_w.append(all_tiles.index(tiles_k[a]))
        tilemap.append(tilemap_w)
    return tiles, tilemap


JUMP_OP = p8(0xC3)
CALL_OP = p8(0xCD)

NEW_FONT_OFFSET = 0x40000

data = open(sys.argv[1], "rb").read()
data = data + b"\x00"*(0x80000-len(data))

for bank in range(0x01, 0x20):
    patch((bank * 0x4000) + 0x3FFE, p8(bank))

font = open("galmuri.fnt", "rb").read()
patch(NEW_FONT_OFFSET, font)

def get_font(char):
    hangul = codecs.open(u"완성형.txt", "r", "UTF-16").read()
    idx = hangul.find(char)
    if idx == -1:
        idx = ":SeHwa".find(char)
        makers_tiles = [
            b"\x00\x00\x18\x18\x18\x18\x00\x00\x00\x00\x18\x18\x18\x18\x00\x00",
            b"\x3C\x3C\x66\x66\x70\x70\x3C\x3C\x0E\x0E\x66\x66\x3C\x3C\x00\x00",
            b"\x00\x00\x3C\x3C\x66\x66\x66\x66\x7E\x7E\x60\x60\x3E\x3E\x00\x00",
            b"\x66\x66\x66\x66\x66\x66\x7E\x7E\x66\x66\x66\x66\x66\x66\x00\x00",
            b"\x00\x00\x00\x00\x63\x63\x6B\x6B\x6B\x6B\x7F\x7F\x36\x36\x00\x00",
            b"\x00\x00\x00\x00\x1E\x1E\x36\x36\x36\x36\x36\x36\x1F\x1F\x00\x00"
        ]
        return makers_tiles[idx]
    return font[idx*0x10:idx*0x10+0x10]

title_tiledata, title_tilemap = get_title(Image.open("title.png"))
patch(0x83AC, compress_data(title_tiledata))
patch(0x62C4, title_tilemap)

sgb_border_tiledata = get_sgb_border(Image.open("title.png"))
patch(0xDF53, compress_data(sgb_border_tiledata))
patch(0xEE83, b"\x01\x07")

main_text = [ ["  수 사 시 작   ", "  수 사 재 개   ", "  환 경 설 정   "], ["메시지 표시속도 ", "   빠 르 게    ", "    보 통     ", "   느 리 게     ", "  ", "  ", " "], ["  패스워드 입력"], [" 패 스 워 드", "           "] ]
main_text_xy = [ [(4, 4), (4, 9), (4, 14)], [(5, 3), (4, 7), (4, 10), (4, 13), (3, 12), (13, 16), (4, 3)], [(4, 2)], [(6, 4), (6, 3)] ]

main_tiledata, _ = decompress_data(0xA604)
main_tilemap, _ = decompress_data(0x3DB12)
main_tilemap2, _ = decompress_data(0x3DC00)
main_tilemap3, _ = decompress_data(0x3D7D5)
main_tilemap4, _ = decompress_data(0x1B30)
for i in range(7):
    main_tiledata[0x09+i] = b"\x00"*0x10
for i in range(6):
    main_tiledata[0x1A+i] = b"\x00"*0x10

main_text_chrs = "".join(sorted(set("".join(map(lambda x: x.replace(" ", ""), "".join(map(lambda x: "".join(x), main_text)))))))
cnt = len(main_tiledata)
for i in range(len(main_text_chrs)):
    if 0x4B+i >= cnt:
        main_tiledata.append(get_font(main_text_chrs[i]))
    else: main_tiledata[0x4B+i] = get_font(main_text_chrs[i])

main_text10_start_idx = len(main_tiledata)
for i in range(len(main_text[1][0])+1):
    t1 = b""
    t2 = b""
    t3 = b""
    if i == 0 or main_text[1][0][i-1] == " ": t1 = b"\x00"*0x10
    else: t1 = get_font(main_text[1][0][i-1])
    if i == len(main_text[1][0]) or main_text[1][0][i] == " ": t2 = b"\x00"*0x10
    else: t2 = get_font(main_text[1][0][i])
    for j in range(0x10):
        t3 += p8(((t1[j] << 4) & 0xFF) | ((t2[j] >> 4) & 0b1111))
    main_tiledata.append(t3)
patch(0x17200, compress_data(b"".join(main_tiledata)))

tilemap = [ b"".join(main_tilemap), b"".join(main_tilemap2), b"".join(main_tilemap3), b"".join(main_tilemap4) ]
for i in range(len(main_text)):
    for j in range(len(main_text[i])):
        x = main_text_xy[i][j][0]
        y = main_text_xy[i][j][1]
        idx = y * 0x14 + x
        for k in range(len(main_text[i][j])):
            tm = 0x4B + main_text_chrs.find(main_text[i][j][k])
            if main_text[i][j][k] == " ": tm = 0x8C
            if i == 1 and j == 0: tm = main_text10_start_idx + k
            tilemap[i] = tilemap[i][:idx+k] + p8(tm) + tilemap[i][idx+k+1:]
patch(0x3DB12, compress_data(tilemap[0]))
patch(0x3DC00, compress_data(tilemap[1]))
patch(0x3D7D5, compress_data(tilemap[2]))
patch(0x1B30, compress_data(tilemap[3]))

evidence_tiledata, _ = decompress_data(0x9BED)
evidence_tiledata[9] = b"\x00"*0x10
evidence_tiledata[14] = b"\x00"*0x10
evidence_tiledata[15] = b"\x00"*0x10
evidence_text = "사건정리"
for i in range(len(evidence_text)):
    evidence_tiledata[i+10] = get_font(evidence_text[i])
patch(0x9BED, compress_data(b"".join(evidence_tiledata)))

profile_point_tiledata, n = decompress_data(0x9892)
point_text = "범인추리"
for i in range(len(point_text)):
    profile_point_tiledata[i] = get_font(point_text[i])
profile_text = "인물소개"
for i in range(6):
    if i < len(profile_text):
        profile_point_tiledata[i+8] = get_font(profile_text[i])
    else: profile_point_tiledata[i] = b"\x00"*0x10
patch(0x9892, compress_data(b"".join(profile_point_tiledata)))

profile_tilemap_offset = 0x36C1
patch(profile_tilemap_offset+0xD, p8(0x8C))
patch(profile_tilemap_offset+0x14+0xD, b"\x8C\x48\x49\x4A\x4B\x8C\x8C")

point_tilemap_offset = 0x23D5
patch(point_tilemap_offset, b"\x8C\x40\x41\x42\x43\x8C\x8C\x8C")

case12_text = [ ["총 간식 비용 ", "주스  ", "과자  "], ["말았습니다  ", "폐를 끼쳤습니다", "사과드리기  ", "죽겠습니다   ", " ", " "] ]
case12_text_xy = [ [(0, 1), (0, 2), (0, 4)], [(0, 3), (0, 5), (0, 7), (0, 9), (4, 6), (4, 8)] ]
case12_text_chrs = "".join(sorted(set("".join(map(lambda x: x.replace(" ", ""), "".join(map(lambda x: "".join(x), case12_text)))))))

case12_tiledata, _ = decompress_data(0x30ABB)
for i in range(26):
    if i < len(case12_text_chrs):
        case12_tiledata[4+i] = get_font(case12_text_chrs[i])
    else: case12_tiledata[4+i] = b"\x00"*0x10
patch(0x30ABB, compress_data(b"".join(case12_tiledata)))

case1_tilemap, _ = decompress_data(0x30A1C)
case2_tilemap, _ = decompress_data(0x30F2D)
tilemap = [ b"".join(case1_tilemap), b"".join(case2_tilemap) ]
for i in range(len(case12_text)):
    for j in range(len(case12_text[i])):
        x = case12_text_xy[i][j][0]
        y = case12_text_xy[i][j][1]
        idx = y * 0x14 + x
        for k in range(len(case12_text[i][j])):
            tm = 4 + case12_text_chrs.find(case12_text[i][j][k])
            if case12_text[i][j][k] == " ": tm = 0x00
            tilemap[i] = tilemap[i][:idx+k] + p8(tm) + tilemap[i][idx+k+1:]
patch(0x30A1C, compress_data(tilemap[0]))
patch(0x30F2D, compress_data(tilemap[1]))

case_title_tiledata, n = decompress_data(0x9DAC)
for i in [31, 32, 36, 37, 46, 47, 59, 60, 72, 73, 81, 82, 88, 89, 94, 95]:
    case_title_tiledata[i] = b"\x00"*0x10

case1_title_tiles, _ = get_case_title(Image.open("case1_title.bmp"))
case2_title_tiles, _ = get_case_title(Image.open("case2_title.bmp"))
case3_title_tiles, _ = get_case_title(Image.open("case3_title.bmp"))
case_title_tiles = sorted(list(set(case1_title_tiles + case2_title_tiles + case3_title_tiles)))
for i in range(len(case_title_tiles)):
    if 123+i < len(case_title_tiledata):
        case_title_tiledata[123+i] = case_title_tiles[i]
    else: case_title_tiledata.append(case_title_tiles[i])
patch(0x9DAC, compress_data(b"".join(case_title_tiledata)))

case1_title_tilemap_offset = 0x30000
case2_title_tilemap_offset = 0x30168
case3_title_tilemap_offset = 0x302D0

_, case1_tilemap = get_case_title(Image.open("case1_title.bmp"), case_title_tiles)
for i in range(8):
    for j in range(8):
        tm_idx = ((7*0x14)+6) + (i*0x14)+j
        patch(case1_title_tilemap_offset+tm_idx, p8((0xFB+case1_tilemap[i][j]) & 0xFF))

_, case2_tilemap = get_case_title(Image.open("case2_title.bmp"), case_title_tiles)
for i in range(8):
    for j in range(8):
        tm_idx = ((7*0x14)+6) + (i*0x14)+j
        patch(case2_title_tilemap_offset+tm_idx, p8((0xFB+case2_tilemap[i][j]) & 0xFF))

_, case3_tilemap = get_case_title(Image.open("case3_title.bmp"), case_title_tiles)
for i in range(8):
    for j in range(8):
        tm_idx = ((7*0x14)+6) + (i*0x14)+j
        patch(case3_title_tilemap_offset+tm_idx, p8((0xFB+case3_tilemap[i][j]) & 0xFF))


type_text = ["번역 종류 선택 ", "   더 빙 판    ", "   자 막 판     ", "그래픽:피씨", "번역 :가각", "패치 :SeHwa"]
type_text_xy = [(5, 3), (4, 8), (4, 12), (2, 15), (2, 16), (2, 17)]
type_text_chrs = "".join(sorted(set("".join(map(lambda x: x.replace(" ", ""), type_text)))))

main_tiledata, _ = decompress_data(0xA604)
type_tiledata = main_tiledata[:0x26]
for i in range(7):
    type_tiledata[0x09+i] = b"\x00"*0x10
for i in range(6):
    type_tiledata[0x1A+i] = b"\x00"*0x10

for i in range(len(type_text_chrs)):
    type_tiledata.append(get_font(type_text_chrs[i]))
type_text0_start_idx = len(type_tiledata)
for i in range(len(type_text[0])+1):
    t1 = b""
    t2 = b""
    t3 = b""
    if i == 0 or type_text[0][i-1] == " ": t1 = b"\x00"*0x10
    else: t1 = get_font(type_text[0][i-1])
    if i == len(type_text[0]) or type_text[0][i] == " ": t2 = b"\x00"*0x10
    else: t2 = get_font(type_text[0][i])
    for j in range(0x10):
        t3 += p8(((t1[j] << 4) & 0xFF) | ((t2[j] >> 4) & 0b1111))
    type_tiledata.append(t3)

main_tilemap, _ = decompress_data(0x3DC00)
type_tilemap = b"".join(main_tilemap)
for j in range(len(type_text)):
    x = type_text_xy[j][0]
    y = type_text_xy[j][1]
    idx = y * 0x14 + x
    for k in range(len(type_text[j])):
        tm = 0x26 + type_text_chrs.find(type_text[j][k])
        if type_text[j][k] == " ": tm = 0x00
        if j == 0: tm = type_text0_start_idx + k
        type_tilemap = type_tilemap[:idx+k] + p8(tm) + type_tilemap[idx+k+1:]
c1 = compress_data(b"".join(type_tiledata))
c2 = compress_data(type_tilemap)
patch(0x3FB00, compress_data(b"".join(type_tiledata)))
patch(0x3FE00, compress_data(type_tilemap))


PATCH_CODE0_OFFSET = 0x61
PATCH_CODE1_BANK = 0x0F
PATCH_CODE1_ADDR = 0x7A00
PATCH_CODE1_OFFSET = (PATCH_CODE1_BANK * 0x4000) + (PATCH_CODE1_ADDR - 0x4000)
PATCH_CODE_NEWBANK_BANK = 0x16
PATCH_CODE_NEWBANK_ADDR = 0x7500
PATCH_CODE_NEWBANK_OFFSET = (PATCH_CODE_NEWBANK_BANK * 0x4000) + (PATCH_CODE_NEWBANK_ADDR - 0x4000)
PATCH_NEWBANK_HOOK_OFFSET_TABLE_ADDR = 0x7F00
PATCH_NEWBANK_HOOK_OFFSET_TABLE_OFFSET = (PATCH_CODE_NEWBANK_BANK * 0x4000) + (PATCH_NEWBANK_HOOK_OFFSET_TABLE_ADDR - 0x4000)

patch_code = open("output.obj", "rb").read().split(b"\x88\x88\x88\x88")
patch_code0 = patch_code[0].split(b"\x77\x77\x77\x77")
patch_code1 = patch_code[1].split(b"\x77\x77\x77\x77")

newbank_offsets_idx = patch_code[len(patch_code)-1].find(b"\x99\x99\x99\x99")
newbank_offsets_data = patch_code[len(patch_code)-1][:newbank_offsets_idx]
patch_newbank_offsets = [ u32(newbank_offsets_data[i*4:i*4+4]) for i in range(len(newbank_offsets_data) // 4) ]
patch_newbank_addrs = b"".join(map(lambda x: p16(x % 0x4000 + 0x4000) if x >= 0x4000 and x != 0xFFFF else p16(x), patch_newbank_offsets))
patch(PATCH_NEWBANK_HOOK_OFFSET_TABLE_OFFSET, patch_newbank_addrs)

patch_code_newbank = patch_code[len(patch_code)-1][newbank_offsets_idx+4:]
print("Code0 end address : " + hex(PATCH_CODE0_OFFSET + len(b"".join(patch_code0))))
print("Code1 end address : " + hex(PATCH_CODE1_ADDR + len(b"".join(patch_code1))))
print("Code_newbank end address : " + hex(PATCH_CODE_NEWBANK_ADDR + len(patch_code_newbank)))
patch(PATCH_CODE0_OFFSET, b"".join(patch_code0))
patch(PATCH_CODE1_OFFSET, b"".join(patch_code1))
patch(PATCH_CODE_NEWBANK_OFFSET, patch_code_newbank)
patch_code_addr = PATCH_CODE0_OFFSET
for i in range(len(patch_newbank_offsets)):
    patch(patch_newbank_offsets[i], CALL_OP + p16(patch_code_addr))

arr = codecs.open(u"korean.tbl", "rb", "utf8").read().split("\n")
kor_tables = {}
for i in range(len(arr)):
    t = arr[i].split("=")
    kor_tables[t[1]] = t[0]
code_tables = {}
for i in range(len(arr)):
    a = arr[i].split("=")
    code_tables[int(a[0], 16)] = a[1]

def str2code(str):
    global kor_tables

    code = b""
    for i in range(len(str)):
        code += bytes.fromhex(kor_tables[str[i]])
    return code
def code2str(code, length):
    global code_tables

    i = 0
    string = ""
    while True:
        if code[i] >= 0xE0 and code[i] < 0xF0:
            c = code[i] * 0x100 + code[i+1]
            i += 2
        else:
            c = code[i]
            i += 1
        string += code_tables[c]
        if len(string) >= length: break
    return string

kor_tables["’"] = "20"
kor_tables["”"] = "21"
code_tables[0x20] = "’"
code_tables[0x21] = "”"
patch(0x9140, b"\x30\x30\x30\x30\x10\x10\x20\x20\x00\x00\x00\x00\x00\x00\x00\x00")
patch(0x9150, b"\x6C\x6C\x6C\x6C\x24\x24\x48\x48\x00\x00\x00\x00\x00\x00\x00\x00")


def create_text(translated_text_data, tables, data, ptr):
    F9_nargs = [0, 2, 0, 1, 0, 0, 0, 1, 2, 2, 0, 1, 1, 1, 0, 0, 0, 2, 1, 0, 2, 2, 0, 2, 2, 1, 2, 0, 0]
    start_text = 0
    translated_idx = 0
    cur_line_cnt = 0
    result = b""

    def append_text():
        if translated_text_data[translated_idx] == "": return b""
        r = str2code(translated_text_data[translated_idx])
        t = 1
        while True:
            if data[ptr-t] == 0xA4:
                r += p8(0xA4)
                t += 1
            else: break
        return r

    while True:
        if data[ptr] == 0xF7:
            if start_text == 1:
                result += append_text()
                start_text = 0
            result += p8(0xF7)
            translated_idx += 1
            cur_line_cnt = 0
        elif data[ptr] == 0xF8:
            if start_text == 1:
                result += append_text()
                start_text = 0
            result += p8(0xF8) + p8(data[ptr+1])
            translated_idx += 1
            ptr += 1
        elif data[ptr] == 0xF9:
            if start_text == 1:
                result += append_text()
                start_text = 0
            result += p8(0xF9) + p8(data[ptr+1])
            n_arg = F9_nargs[data[ptr+1]]
            result += b"".join(map(lambda x: p8(x), data[ptr+2:ptr+2+n_arg]))
            translated_idx += 1
            ptr += n_arg
            ptr += 1
        elif data[ptr] == 0xFA:
            if start_text == 1:
                result += append_text()
                start_text = 0
            result += p8(0xFA)
            translated_idx += 2
            cur_line_cnt = 0
        elif data[ptr] == 0xFB:
            if start_text == 1:
                result += append_text()
                start_text = 0
            result += p8(0xFB) + p8(data[ptr+1])
            translated_idx += 1
            ptr += 1
        elif data[ptr] == 0xFC:
            if start_text == 1:
                result += append_text()
                start_text = 0
            result += p8(0xFC) + p8(data[ptr+1])
            translated_idx += 1
            ptr += 1
        elif data[ptr] == 0xFD:
            if start_text == 1:
                result += append_text()
                start_text = 0
            result += p8(0xFD)
            translated_idx += 1
            cur_line_cnt += 1
            if cur_line_cnt >= 3:
                cur_line_cnt = 0
                translated_idx += 1
        elif data[ptr] == 0xFE:
            if start_text == 1:
                result += append_text()
                start_text = 0
            result += p8(0xFE)
            translated_idx += 1
        elif data[ptr] == 0xFF:
            if start_text == 1:
                result += append_text()
                start_text = 0
            result += p8(0xFF)
            translated_idx += 2
            cur_line_cnt = 0
            break
        else:
            if start_text == 0:
                t = 0
                while True:
                    if data[ptr+t] == 0xA4:
                        result += p8(0xA4)
                        t += 1
                    else: break
            start_text = 1
        ptr += 1
    ptr += 1
    return result, translated_text_data[translated_idx:], ptr

bank_text_offset = [0x4000]*0x20
bank_text_offset[0x12] = 0x5300

def patch_text(bank, offset, text):
    patch(offset, p16(bank_text_offset[bank]))
    patch(bank * 0x4000 + (bank_text_offset[bank] - 0x4000), text)
    bank_text_offset[bank] += len(text)

translated_text_data = codecs.open(u"translated_text.txt", "rb", "utf8").read().split("\r\n")
translated_text_data2 = codecs.open(u"translated_text2.txt", "rb", "utf8").read().split("\r\n")
text_set_offset_addrs = [(0x3DC1, 0x3DB9, 0x3DBD), (0x2719, 0x271E, 0x2722), (0x2809, 0x280D, 0x2811), (0x0, 0x29E7, 0x29EB), (0x0, 0x2AAF, 0x2AB3)]
text_offsets = [(0x3DD9, 1), (0x2D68A, 2), (0x2D754, 2), (0x2D80E, 2), (0x2D856, 2)]
for i in range(len(text_offsets)):
    ptr = text_offsets[i][0]
    count = text_offsets[i][1]
    result_all = b""
    for j in range(count):
        _, translated_text_data2, _ = create_text(translated_text_data2, kor_tables, data, ptr)
        result, translated_text_data, ptr = create_text(translated_text_data, kor_tables, data, ptr)
        result_all += result

    offset_bank = text_set_offset_addrs[i][0]
    offset_low = text_set_offset_addrs[i][1]
    offset_high = text_set_offset_addrs[i][2]
    if offset_bank != 0:
        patch(offset_bank, p8(0x12))
    patch(offset_low, p16(bank_text_offset[0x12])[:1])
    patch(offset_high, p16(bank_text_offset[0x12])[1:])

    patch(0x12 * 0x4000 + (bank_text_offset[0x12] - 0x4000), result_all)
    bank_text_offset[0x12] += len(result_all)

text_ptr_table_offsets = [(0x29F3, 5), (0x48E5, 30), (0x4BF6, 10), (0x22A8A, 68), (0x23C38, 7), (0x25B16, 17), (0x2AB05, 19), (0x2C000, 18), (0x2C945, 12), (0x2D05E, 10), (0x2D4E4, 5), (0x2D9A9, 19), (0x2F4C9, 50)]
ptr_tables = []
for i in range(len(text_ptr_table_offsets)):
    offset = text_ptr_table_offsets[i][0]
    count = text_ptr_table_offsets[i][1]
    last_addr = 0
    for j in range(count):
        bank = offset // 0x4000
        addr = u16(data[offset+(j*2):offset+(j*2)+2])
        ptr_tables.append((bank, addr))
        if addr == 0x0 or addr == 0xffff: continue
        if last_addr < addr: last_addr = addr
    for j in range(count):
        result_all = b""
        result2_all = b""
        bank = offset // 0x4000
        addr = u16(data[offset+(j*2):offset+(j*2)+2])
        addr_orig = addr
        if addr == 0xffff:
            patch(offset+(j*2), p16(0xffff))
            patch(offset+(count*2)+(j*2), p16(0xffff))
            continue
        if addr == 0x0: continue
        if addr >= 0x4000: addr -= 0x4000
        ptr = bank * 0x4000 + addr
        while True:
            result, translated_text_data, end_ptr = create_text(translated_text_data, kor_tables, data, ptr)
            result2, translated_text_data2, _ = create_text(translated_text_data2, kor_tables, data, ptr)
            if end_ptr == 0x2BEF9 or end_ptr == 0x2F4C9: # hack
                result_all += result
                result2_all += result2
                break
            if addr_orig != last_addr:
                find = -1
                for k in range(len(ptr_tables)):
                    bank = ptr_tables[k][0]
                    addr = ptr_tables[k][1]
                    if addr == int(not not bank) * 0x4000 + (end_ptr % 0x4000):
                        find = 1
                        break
                if find == -1:
                    result_all += result
                    result2_all += result2
                    ptr = end_ptr
                    continue
            result_all += result
            result2_all += result2
            break

        if i == 0 or i == 2 or i == 4:
            patch_text(0x12, offset+(j*2), result_all)
            patch_text(0x12, offset+(count*2)+(j*2), result2_all)
        elif i == 1:
            f = 0
            char_len = 0
            tmp = result_all[:-1]
            while True:
                if tmp[-1] != 0xA4: break
                tmp = tmp[:-1]
            if result_all[0] == 0xFB: tmp = tmp[2:]
            for k in range(len(tmp)):
                if f == 1:
                    f = 0
                    continue
                if tmp[k] >= 0xE0 and tmp[k] <= 0xE9: f = 1
                char_len += 1
            tmp = tmp + b"\xA4"*(8 - char_len)
            if result_all[0] == 0xFB: result_all = result_all[:2] + tmp
            else: result_all = tmp
            result_all += b"\xFF"

            patch_text(0x12, offset+(j*2), result_all)

            f = 0
            char_len = 0
            tmp = result2_all[:-1]
            while True:
                if tmp[-1] != 0xA4: break
                tmp = tmp[:-1]
            if result2_all[0] == 0xFB: tmp = tmp[2:]
            for k in range(len(tmp)):
                if f == 1:
                    f = 0
                    continue
                if tmp[k] >= 0xE0 and tmp[k] <= 0xE9: f = 1
                char_len += 1
            tmp = tmp + b"\xA4"*(8 - char_len)
            if result2_all[0] == 0xFB: result2_all = result2_all[:2] + tmp
            else: result2_all = tmp
            result2_all += b"\xFF"

            patch_text(0x12, offset+(count*2)+6+(j*2), result2_all)
        elif i == 3:
            patch_text(0x13, offset+(j*2), result_all)
            patch_text(0x13, offset+(count*2)+(j*2), result2_all)
        elif i == 5:
            patch_text(0x14, offset+(j*2), result_all)
            patch_text(0x15, offset+(count*2)+(j*2), result2_all)
        elif i == 6:
            patch_text(0x16, offset+(j*2), result_all)
            patch_text(0x16, offset+(count*2)+(j*2), result2_all)
        elif i == 7:
            patch_text(0x19, offset+(j*2), result_all)
            patch_text(0x19, offset+(count*2)+(j*2), result2_all)
        elif i == 8:
            patch_text(0x17, offset+(j*2), result_all)
            patch_text(0x17, offset+(count*2)+(j*2), result2_all)
        elif i == 9:
            patch_text(0x18, offset+(j*2), result_all)
            patch_text(0x18, offset+(count*2)+(j*2), result2_all)
        elif i == 10:
            patch_text(0x18, offset+(j*2), result_all)
            patch_text(0x18, offset+(count*2)+(j*2), result2_all)
        elif i == 11:
            patch_text(0x17, offset+(j*2), result_all)
            patch_text(0x18, offset+(count*2)+(j*2), result2_all)
        elif i == 12:
            patch_text(0x19, offset+(j*2), result_all)
            patch_text(0x19, offset+(count*2)+(j*2), result2_all)
    if i == 1:
        patch(offset+(count*2), p16(offset+(count*2)+6+0x00))
        patch(offset+(count*2)+2, p16(offset+(count*2)+6+0x14))
        patch(offset+(count*2)+4, p16(offset+(count*2)+6+0x28))

        patch(0x1A18, p16(bank_text_offset[0x12]))
        patch(0x1AA2, p16(bank_text_offset[0x12]))
        patch(0x3A1A,  p8(p16(bank_text_offset[0x12])[0]))
        patch(0x3A1E,  p8(p16(bank_text_offset[0x12])[1]))
        patch(0x3B74,  p8(p16(bank_text_offset[0x12])[0]))
        patch(0x3B78,  p8(p16(bank_text_offset[0x12])[1]))
        patch(0x3B87, p8(0x12))
        patch(0x3994, p8(0x12))
        patch(0x12 * 0x4000 + (bank_text_offset[0x12] - 0x4000), b"\xA4"*8 + b"\xFF")
        bank_text_offset[0x12] += 9
    elif i == 2:
        patch(0x391F, p8(0x12))
    elif i == 3:
        patch(0x16CA, p8(0x13))
    elif i == 4:
        patch(0x1B0C, p8(0x12))
    elif i == 5:
        patch(0x2125, b"\x00"*2)

TEXT_LOC_TABLE_OFFSET = 0x2D42

for i in range(4):
    bank = data[TEXT_LOC_TABLE_OFFSET+(i*3)]
    addr = u16(data[TEXT_LOC_TABLE_OFFSET+(i*3)+1:TEXT_LOC_TABLE_OFFSET+(i*3)+3])
    offset = bank * 0x4000 + (addr - 0x4000)
    count = (u16(data[offset:offset+2]) - addr) // 2
    ptr_tables = []
    last_addr = 0
    for j in range(count):
        addr = u16(data[offset+(j*2):offset+(j*2)+2])
        ptr_tables.append(addr)
        if last_addr < addr: last_addr = addr
    for j in range(count):
        result_all = b""
        result2_all = b""
        addr = ptr_tables[j]
        ptr = bank * 0x4000 + (addr - 0x4000)
        while True:
            result, translated_text_data, end_ptr = create_text(translated_text_data, kor_tables, data, ptr)
            result2, translated_text_data2, _ = create_text(translated_text_data2, kor_tables, data, ptr)
            if i == 2 and j == 62: # hack
                if end_ptr == 0x3A4EC:
                    result_all += result
                    result2_all += result2
                    ptr = end_ptr
                    continue

            if ptr_tables[j] != last_addr:
                find = -1
                for k in range(count):
                    addr = ptr_tables[k]
                    if addr == int(not not bank) * 0x4000 + (end_ptr % 0x4000):
                        find = 1
                        break
                if find == -1:
                    result_all += result
                    result2_all += result2
                    ptr = end_ptr
                    continue
            result_all += result
            result2_all += result2
            break

        if i == 0:
            patch_text(0x1A, offset+(j*2), result_all)
            patch_text(0x1B, offset+(count*2)+(j*2), result2_all)
        elif i == 1:
            if j < 27:
                patch_text(0x14, offset+(j*2), result_all)
            else:
                patch_text(0x1E, offset+(j*2), result_all)

            if j < 27:
                patch_text(0x15, offset+(count*2)+(j*2), result2_all)
            else:
                patch_text(0x1F, offset+(count*2)+(j*2), result2_all)
        elif i == 2:
            patch_text(0x1C, offset+(j*2), result_all)
            patch_text(0x1D, offset+(count*2)+(j*2), result2_all)
        elif i == 3:
            patch_text(0x12, offset+(j*2), result_all)
            patch_text(0x12, offset+(count*2)+(j*2), result2_all)

hidden_scenario_text_offsets = [0x3C433, 0x3C485, 0x3C539, 0x3C53D, 0x3C575, 0x3C5B3]
new_ptr_table_offset = 0x3FFA0
last_addr = 0x3C5F8

patch(0x3C41F, p8(0x13))
for i in range(len(hidden_scenario_text_offsets)):
    ptr = hidden_scenario_text_offsets[i]
    result_all = b""
    result2_all = b""
    while True:
        result, translated_text_data, _ = create_text(translated_text_data, kor_tables, data, ptr)
        result2, translated_text_data2, ptr = create_text(translated_text_data2, kor_tables, data, ptr)
        result_all += result
        result2_all += result2
        if ptr == last_addr: break

    patch_text(0x13, new_ptr_table_offset+(i*2), result_all)
    patch_text(0x13, new_ptr_table_offset+(len(hidden_scenario_text_offsets)*2)+(i*2), result2_all)

hidden_scenario_ptr_table_offsets = [(0x3C3E0, 4)]
new_ptr_table_offset = 0x3FFC0
for i in range(len(hidden_scenario_ptr_table_offsets)):
    offset = hidden_scenario_ptr_table_offsets[i][0]
    count = hidden_scenario_ptr_table_offsets[i][1]
    for j in range(count):
        result_all = b""
        result2_all = b""
        bank = offset // 0x4000
        addr = u16(data[offset+(j*2):offset+(j*2)+2])
        addr_orig = addr
        if addr >= 0x4000: addr -= 0x4000
        ptr = bank * 0x4000 + addr
        while True:
            result, translated_text_data, _ = create_text(translated_text_data, kor_tables, data, ptr)
            result2, translated_text_data2, ptr = create_text(translated_text_data2, kor_tables, data, ptr)
            result_all += result
            result2_all += result2
            if ptr == last_addr: break

        patch_text(0x1A, new_ptr_table_offset+(j*2), result_all)
        patch_text(0x1A, new_ptr_table_offset+(count*2)+(j*2), result2_all)

for i in range(0x12, 0x20):
    print("bank%X end address : %04x" % (i, bank_text_offset[i]))

patch(0x8EE0, b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x30\x30\x10\x10\x20\x20")
patch(0x4032, str2code("인물소개     사건정리") + b"\xFD" + str2code("패스워드"))


patch(0x148, b"\x04")
patch(0x14D, p8(gb_checksum1(data_patched)))
patch(0x14E, pb16(gb_checksum2(data_patched)))

open("output.gb", "wb").write(data_patched)
