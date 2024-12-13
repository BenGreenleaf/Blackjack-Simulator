vals = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'j', 'q', 'k', 'a']
suits = ['s', 'c', 'h', 'd']

deck = []
decks = 2 #number of decks

for i in range(0,decks):
    for i in suits:
        for j in vals:
            deck.append(i+j)
            

def removeCard(card):
    deck.remove(card)

def toValue(card):
    value = 0
    try:
        if len(card) == 2:
            value = int(card[-1])
        else:
            value = 10    
        
    except:
        if card[:-1] == "j" or card[-1] == "q" or card[-1] == "k":
            value = 10
        elif card[:1] == "a":
            value = 11


    return(value)        

def calculateDecision(c1, c2, d1):
    v1 = toValue(c1)
    v2 = toValue(c2)

    v3 = toValue(d1)

    total = v1 + v2

    visited = 0
    temp = 0
    loss = 0
    win = 0

    for i in deck:
        visited += 1
        temp = toValue(i)

        if total + temp > 21:
            loss += 1
        else:
            win += 1


    safeProb = win/visited
    return(safeProb)

while True:
    first = str(input("1st Card"))
    second = str(input("2nd Card"))

    dealr = str(input("Enter Dealers Card"))

    removeCard(first)
    removeCard(second)
    removeCard(dealr)

    print(calculateDecision(first,second,dealr))
    print("\n")









