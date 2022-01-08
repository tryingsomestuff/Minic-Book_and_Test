pieces_lst = []
for line in open("frc_openings.pgn"):
    if line.find("FEN") < 0: continue
    fen = line.split('"')[1]
    pieces_lst.append(fen.split("/")[0])

def get_castling_flags(pieces):
    pos1 = pieces.index("r")
    pos2 = pos1 + 1 + pieces[pos1+1:].index("r")
    return "abcdefgh"[pos2]+"abcdefgh"[pos1]
    
with open("dfrc_openings.pgn", "w") as fp_out:
    for white in range(len(pieces_lst)):
        for black in range(len(pieces_lst)):
            castling_flags = get_castling_flags(pieces_lst[white]).upper() + get_castling_flags(pieces_lst[black])
            fen = f"{pieces_lst[black]}/pppppppp/8/8/8/8/PPPPPPPP/{pieces_lst[white].upper()} w {castling_flags} - 0 1"
            fp_out.write(f"""[Variant "fischerandom"]
[Round "{white}.{black}"]
[FEN "{fen}"]

*

""")
