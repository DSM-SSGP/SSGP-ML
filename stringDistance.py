def n_gram(str, n=2):
    return [str[i:i+n] for i in range(len(str)-n+1)]

def subst_dist(str1, str2):
    def subst(x, y):
        return sum(s not in y for s in n_gram(x, 2)) / (len(x) - 1)
    return (subst(str1, str2) + subst(str2, str1)) / 2