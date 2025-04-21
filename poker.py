import random
import itertools
from collections import Counter

def determine_hand(hand):
    """
    Determine the type of poker hand and return information for kicker comparison.
    
    Args:
        hand: A list of 5 tuples (rank, suit) representing cards
        
    Returns:
        A tuple of (hand_type, tiebreaker_values) where tiebreaker_values is a list
        of values used for comparing hands of the same type
    """
    # Extract ranks and suits
    ranks = [card[0] for card in hand]
    suits = [card[1] for card in hand]
    
    # Convert face cards to numeric values for easier comparison
    rank_values = []
    for rank in ranks:
        if rank == 'A':
            rank_values.append(14)
        elif rank == 'K':
            rank_values.append(13)
        elif rank == 'Q':
            rank_values.append(12)
        elif rank == 'J':
            rank_values.append(11)
        else:
            rank_values.append(int(rank))
    
    # Sort ranks for easier straight detection
    rank_values.sort(reverse=True)  # Sort in descending order for easier kicker comparison
    
    # Check for flush (all same suit)
    is_flush = len(set(suits)) == 1
    
    # Check for straight (consecutive values)
    is_straight = False
    if len(set(rank_values)) == 5:  # All distinct ranks
        if max(rank_values) - min(rank_values) == 4:
            is_straight = True
        # Special case for A-5 straight
        elif set(rank_values) == {14, 5, 4, 3, 2}:
            is_straight = True
            # A-5 straight has 5 as the high card
            rank_values = [5, 4, 3, 2, 1]  # Adjust values for correct comparison
    
    # Count rank frequencies
    rank_counts = Counter(rank_values)
    
    # Identify hand type
    if is_straight and is_flush:
        if rank_values == [14, 13, 12, 11, 10]:  # A, K, Q, J, 10
            return ("Royal Flush", rank_values)
        return ("Straight Flush", rank_values)
    
    if 4 in rank_counts.values():
        quads = [r for r, count in rank_counts.items() if count == 4][0]
        kicker = [r for r, count in rank_counts.items() if count == 1][0]
        return ("Four of a Kind", [quads, kicker])
    
    if 3 in rank_counts.values() and 2 in rank_counts.values():
        trips = [r for r, count in rank_counts.items() if count == 3][0]
        pair = [r for r, count in rank_counts.items() if count == 2][0]
        return ("Full House", [trips, pair])
    
    if is_flush:
        return ("Flush", rank_values)
    
    if is_straight:
        return ("Straight", rank_values)
    
    if 3 in rank_counts.values():
        trips = [r for r, count in rank_counts.items() if count == 3][0]
        kickers = sorted([r for r, count in rank_counts.items() if count == 1], reverse=True)
        return ("Three of a Kind", [trips] + kickers)
    
    if list(rank_counts.values()).count(2) == 2:
        pairs = sorted([r for r, count in rank_counts.items() if count == 2], reverse=True)
        kicker = [r for r, count in rank_counts.items() if count == 1][0]
        return ("Two Pair", pairs + [kicker])
    
    if 2 in rank_counts.values():
        pair = [r for r, count in rank_counts.items() if count == 2][0]
        kickers = sorted([r for r, count in rank_counts.items() if count == 1], reverse=True)
        return ("One Pair", [pair] + kickers)
    
    return ("High Card", rank_values)

def calculate_winning_probability(my_hand, community_cards, num_opponents, num_simulations=10000):
    """
    Calculate the probability of winning with your hand against a number of opponents.
    
    Args:
        my_hand: A list of 2 tuples (rank, suit) representing your hole cards
        community_cards: A list of 0-5 tuples (rank, suit) for the community cards
        num_opponents: Number of other players
        num_simulations: Number of random scenarios to simulate
        
    Returns:
        Probability of winning as a float between 0 and 1
    """
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    suits = ['♠', '♥', '♦', '♣']
    
    # Create a full deck
    full_deck = [(rank, suit) for rank in ranks for suit in suits]
    
    # Remove cards that are already in play
    available_cards = [card for card in full_deck if card not in my_hand and card not in community_cards]
    
    wins = 0
    ties = 0
    
    for _ in range(num_simulations):
        # Shuffle the available cards
        random.shuffle(available_cards)
        current_deck = available_cards.copy()
        
        # Deal cards to opponents
        opponent_hands = []
        for _ in range(num_opponents):
            opponent_hand = [current_deck.pop() for _ in range(2)]
            opponent_hands.append(opponent_hand)
        
        # Complete the community cards if needed
        remaining_community = 5 - len(community_cards)
        simulation_community = community_cards.copy()
        
        if remaining_community > 0:
            simulation_community.extend([current_deck.pop() for _ in range(remaining_community)])
        
        # Determine the best hand for each player
        my_best_hand = find_best_hand(my_hand, simulation_community)
        
        # Check against all opponents
        is_win = True
        is_tie = False
        
        for opp_hand in opponent_hands:
            opp_best_hand = find_best_hand(opp_hand, simulation_community)
            comparison = compare_hands(my_best_hand, opp_best_hand)
            
            if comparison < 0:  # Opponent has better hand
                is_win = False
                is_tie = False
                break
            elif comparison == 0:  # Tie with at least one opponent
                is_win = False
                is_tie = True
        
        if is_win:
            wins += 1
        elif is_tie:
            ties += 0.5  # Count ties as half-wins
    
    return (wins + ties) / num_simulations

def find_best_hand(hole_cards, community_cards):
    """Find the best 5-card hand from hole cards and community cards"""
    all_cards = hole_cards + community_cards
    all_possible_hands = list(itertools.combinations(all_cards, 5))
    
    best_hand = None
    best_hand_info = None
    
    for hand in all_possible_hands:
        hand_info = determine_hand(hand)
        if best_hand is None or compare_hand_info(hand_info, best_hand_info) > 0:
            best_hand = hand
            best_hand_info = hand_info
    
    return best_hand

def compare_hands(hand1, hand2):
    """
    Compare two hands (5 cards each)
    Returns:
        1 if hand1 is better, -1 if hand2 is better, 0 if exactly equal
    """
    hand1_info = determine_hand(hand1)
    hand2_info = determine_hand(hand2)
    return compare_hand_info(hand1_info, hand2_info)

def compare_hand_info(hand1_info, hand2_info):
    """
    Compare two hand info tuples (hand_type, tiebreaker_values)
    Returns:
        1 if hand1 is better, -1 if hand2 is better, 0 if exactly equal
    """
    hand_types = [
        "High Card",
        "One Pair",
        "Two Pair",
        "Three of a Kind",
        "Straight",
        "Flush",
        "Full House",
        "Four of a Kind",
        "Straight Flush",
        "Royal Flush"
    ]
    
    hand1_type, hand1_values = hand1_info
    hand2_type, hand2_values = hand2_info
    
    rank1 = hand_types.index(hand1_type)
    rank2 = hand_types.index(hand2_type)
    
    if rank1 > rank2:
        return 1
    elif rank1 < rank2:
        return -1
    else:
        # Same hand type, compare kickers
        for val1, val2 in zip(hand1_values, hand2_values):
            if val1 > val2:
                return 1
            elif val1 < val2:
                return -1
        
        # If we get here, hands are identical
        return 0


def calculate_best_decision(my_hand, community_cards, num_opponents, pot_size, current_bet, my_stack, opponent_stacks=None, num_simulations=1000):
    """
    Calculate the expected value (EV) of different decisions and return the best one.
    Uses Kelly criterion for optimal bet sizing.
    
    Args:
        my_hand: A list of 2 tuples (rank, suit) representing your hole cards
        community_cards: A list of 0-5 tuples (rank, suit) for the community cards
        num_opponents: Number of other players
        pot_size: Current size of the pot
        current_bet: Amount you need to call
        my_stack: Your remaining stack
        opponent_stacks: List of opponent stack sizes (optional)
        num_simulations: Number of random scenarios to simulate
        
    Returns:
        A tuple of (best_decision, expected_value) where best_decision is one of:
        "fold", "call", or "raise X" where X is the optimal raise amount
    """
    # Calculate probability of winning
    win_probability = calculate_winning_probability(my_hand, community_cards, num_opponents, num_simulations)
    
    # Calculate EV of folding (always 0)
    fold_ev = 0
    
    # Calculate EV of calling
    call_ev = win_probability * (pot_size + current_bet) - (1 - win_probability) * current_bet
    
    # If we can't even call, we must fold or go all-in
    if current_bet >= my_stack:
        if call_ev > fold_ev:
            return ("all-in", call_ev)
        else:
            return ("fold", fold_ev)
    
    # Apply Kelly criterion to determine optimal bet size
    # Kelly fraction = (bp - q) / b where:
    # p = probability of winning
    # q = probability of losing (1-p)
    # b = odds received (pot / bet)
    
    odds = pot_size / current_bet if current_bet > 0 else float('inf')
    kelly_fraction = (odds * win_probability - (1 - win_probability)) / odds
    
    # Limit Kelly to a more conservative fraction (half Kelly)
    kelly_fraction = max(0, kelly_fraction * 0.3)
    
    # Kelly-recommended bet size
    kelly_bet = min(kelly_fraction * my_stack, my_stack)
    
    # Ensure kelly_bet is at least the current bet (to call)
    kelly_bet = max(kelly_bet, current_bet)
    
    # Calculate EV of raising according to Kelly
    if kelly_bet > current_bet:
        # Simple EV calculation for the Kelly bet
        raise_amount = kelly_bet
        fold_probability = min(0.1 + (raise_amount / pot_size) * 0.4, 0.8)
        
        # If opponents fold
        ev_fold = fold_probability * pot_size
        
        # If opponents call
        call_pot = pot_size + raise_amount + (raise_amount - current_bet)
        ev_call_win = (1 - fold_probability) * win_probability * call_pot
        ev_call_lose = (1 - fold_probability) * (1 - win_probability) * raise_amount
        
        raise_ev = ev_fold + ev_call_win - ev_call_lose
        
        # Choose the action with the highest EV
        if raise_ev > call_ev and raise_ev > fold_ev:
            return (f"raise {int(raise_amount)}", raise_ev)
    
    # If Kelly doesn't suggest a raise or it's not favorable
    if call_ev > fold_ev:
        return ("call", call_ev)
    else:
        return ("fold", fold_ev)
    

# Example usage of calculate_best_decision
if __name__ == "__main__":
    # Example hands
    # Format: (rank, suit)
    # Suits: ♠ (spades), ♥ (hearts), ♦ (diamonds), ♣ (clubs)
    
    # Example 1: Strong starting hand pre-flop
    my_hand = [('A', '♠'), ('A', '♥')]  # Pocket aces
    community_cards = []  # Pre-flop
    win_prob = calculate_winning_probability(my_hand, community_cards, 3)
    print(f"Pocket aces probability against 3 opponents: {win_prob:.4f}")
    
    decision, ev = calculate_best_decision(my_hand, community_cards, 3, pot_size=100, current_bet=50, my_stack=1000)
    print(f"Best decision: {decision} (EV: {ev:.2f})\n")
    
    # Example 2: With flop
    my_hand = [('K', '♥'), ('Q', '♥')]  # King-Queen suited
    community_cards = [('J', '♥'), ('10', '♠'), ('2', '♣')]  # Flop with open-ended straight draw
    win_prob = calculate_winning_probability(my_hand, community_cards, 2)
    print(f"K♥-Q♥ with flop J♥-10♠-2♣ against 2 opponents: {win_prob:.4f}")
    
    decision, ev = calculate_best_decision(my_hand, community_cards, 2, pot_size=250, current_bet=75, my_stack=800)
    print(f"Best decision: {decision} (EV: {ev:.2f})\n")
    
    # Example 3: With turn
    my_hand = [('7', '♣'), ('7', '♠')]  # Pocket sevens
    community_cards = [('2', '♥'), ('7', '♥'), ('K', '♠'), ('A', '♦')]  # Turn with trips
    win_prob = calculate_winning_probability(my_hand, community_cards, 1)
    print(f"Pocket 7s with turn 2♥-7♥-K♠-A♦ against 1 opponent: {win_prob:.4f}")
    
    decision, ev = calculate_best_decision(my_hand, community_cards, 1, pot_size=400, current_bet=150, my_stack=600)
    print(f"Best decision: {decision} (EV: {ev:.2f})")