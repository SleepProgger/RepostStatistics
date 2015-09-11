import functools

def formatit(elems, value):
    for pval, pname in elems[::-1]:
        if pval <= value:
            return "%.1f %s" % (value / pval, pname)
    return "%.1f %s" % (value, elems[0][1])

crudeTimeFormat = functools.partial(formatit, ((1.0, "seconds"), (60.0, "minutes"), (60.0*60.0, "hours"), (60.0*60.0*24.0, "days"), (7.0*60.0*60.0*24.0, "weeks"), (60.0*60.0*24.0*356, "years")))

if __name__ == '__main__':
    print crudeTimeFormat(60.0*60.0*24.0*35.0)