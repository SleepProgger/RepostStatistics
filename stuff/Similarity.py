from itertools import imap
import operator

def hamming(strA, strB):
    return sum(imap(operator.ne, strA, strB))


# http://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)
    previous_row = xrange(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

# normalised levenshtein
def levenshtein_n(s1, s2):
    if len(s1)+len(s2) == 0: return 0
    return levenshtein(s1, s2) / float(max(len(s1), len(s2)))

if __name__ == '__main__':
    while True:
        sa = raw_input("Word A:")
        sb = raw_input("Word B:")
        print "max word len", max(len(sa), len(sb))
        print "hamming:", hamming(sa, sb)
        print "levenshtein:", levenshtein(sa, sb)
        print "levenshtein_n:", levenshtein_n(sa, sb)
        print "stars from 5:", (1-levenshtein_n(sa, sb))*5
#        round(5 * (1 - (levenshtein(t1, t2) / max(len(t1), len(t2))))) 
