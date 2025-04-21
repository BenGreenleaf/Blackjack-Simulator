import random
import itertools
from collections import Counter
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

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


def calculate_best_decision(my_hand, community_cards, num_opponents, pot_size, current_bet, my_stack, previously_betted, opponent_stacks=None, num_simulations=1000):
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


    # Calcualte total staked
    potential_total_loss = previously_betted+current_bet
    potential_pot_size = pot_size+current_bet
    
    # Calculate EV of calling
    call_ev = win_probability * (potential_pot_size) - (1 - win_probability) * potential_total_loss
    
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
    
    print("Potential Pot Size:", potential_pot_size)
    print("Potential Total Loss:", potential_total_loss)
    odds = potential_pot_size / potential_total_loss
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
    

def parse_card(card_text):
    """Parse a card string like '10♠' into ('10', '♠')"""
    if not card_text:
        return None
    
    suits = ['♠', '♥', '♦', '♣']
    suit = next((s for s in suits if s in card_text), None)
    if not suit:
        return None
        
    rank = card_text.replace(suit, '')
    return (rank, suit)

def scrape_pokernow(game_url):
    """
    Scrape the current game state from PokerNow website
    
    Args:
        game_url: URL of the PokerNow game
        
    Returns:
        Dictionary containing game state information:
        {
            'my_hand': List of 2 tuples (rank, suit),
            'community_cards': List of 0-5 tuples (rank, suit),
            'pot_size': Current pot size (float),
            'current_bet': Current bet to call (float),
            'my_stack': Your stack size (float),
            'num_opponents': Number of active opponents (int),
            'opponent_stacks': List of opponent stack sizes
        }
    """
    # Set up headless Chrome
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=chrome_options)
    

    driver.get(game_url)
    
    # Wait for the seat button to be available
    try:
        seat_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "table-player-seat-button"))
        )
        seat_button.click()
        # Wait briefly for any animations or state changes after clicking
        time.sleep(1)

        # Find the form for entering player details
        form = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "form-1"))
        )

        nickname_input = form.find_element(By.CSS_SELECTOR, "div:nth-child(1) > input[type=text]")
        nickname_input.clear()
        nickname_input.send_keys("guest")
        time.sleep(1)
        # Find the stack input and enter a value
        stack_input = form.find_element(By.CSS_SELECTOR, "div:nth-child(2) > input[type=text]")
        stack_input.clear()
        stack_input.send_keys("1000")  # Entering a default stack value of 1000
        time.sleep(1)

        # Click the "Take the Seat" button
        submit_button = form.find_element(By.CSS_SELECTOR, "button")
        submit_button.click()

        # Wait for the form to be processed
        time.sleep(2)
    except Exception as e:
        print(f"Error clicking seat button: {e}")

    time.sleep(20)
    # Let's extract game state information from the page
    previously_betted = 0
    previous_bet = 0
    last_cards = []
    while True:
        time.sleep(1)
    
        # Wait for the table to load completely
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "seats"))
        )
        
        # Find my cards
        my_hand = []
        my_player = driver.find_element(By.CLASS_NAME, "you-player")
        card_containers = my_player.find_elements(By.CLASS_NAME, "card-container.flipped")
        
        for card_container in card_containers:
            card_value = card_container.find_element(By.CLASS_NAME, "value").text
            card_suit = card_container.find_element(By.CSS_SELECTOR, "div > div.card > span:nth-child(3)").text
            
            # Convert suit text to symbol
            suit_map = {'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'}
            suit_symbol = suit_map.get(card_suit.lower(), card_suit)
            
            my_hand.append((card_value, suit_symbol))
        
        if my_hand != last_cards:
            previously_betted = 0

        last_cards = my_hand.copy()

        # Find community cards
        community_cards = []
        try:
            # Find the table cards container
            community_cards_container = driver.find_element(By.CLASS_NAME, "table-cards")
            community_card_containers = community_cards_container.find_elements(By.CLASS_NAME, "card-container.flipped")
            
            for card_container in community_card_containers:
                # Find the card element
                card_element = card_container.find_element(By.CLASS_NAME, "card")
                card_value = card_element.find_element(By.CLASS_NAME, "value").text
                card_suit = card_element.find_element(By.CLASS_NAME, "suit:not(.sub-suit)").text
                
                # Convert suit text to symbol
                suit_map = {'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'}
                suit_symbol = suit_map.get(card_suit.lower(), card_suit)
                
                # Handle special card values that might appear in different formats
                if card_value == "T":
                    card_value = "10"
                    
                community_cards.append((card_value, suit_symbol))
        except Exception as e:
            print(f"Error getting community cards: {e}")
            # Might not have community cards yet
            pass
        
        # Get pot size
        try:
            pot_container = driver.find_element(By.CLASS_NAME, "table-pot-size")
            
            # First try to get the total from add-on-container if it exists
            try:
                add_on_container = pot_container.find_element(By.CLASS_NAME, "add-on-container")
                pot_value_element = add_on_container.find_element(By.CSS_SELECTOR, ".add-on .chips-value .normal-value")
                pot_size = float(pot_value_element.text)
            except:
                # If add-on-container doesn't exist or has issues, fall back to the main value
                pot_value_element = pot_container.find_element(By.CSS_SELECTOR, ".main-value .chips-value .normal-value")
                pot_size = float(pot_value_element.text)
            
        except Exception as e:
            print(f"Error getting pot size: {e}")
            pot_size = 0
        
        # Get my stack
        my_stack_text = my_player.find_element(By.CLASS_NAME, "table-player-stack").text
        my_stack = float(re.search(r'\d+', my_stack_text).group())

        try:
            bet_amount = int(my_player.find_element(By.CSS_SELECTOR, "p > span > span").text) + previously_betted
        except:
            previously_betted = bet_amount
            print("No bet amount found, setting to 0")
        
        # Get current bet to call
        try:
            # First try to find the 'Call' button that shows the bet amount
            call_buttons = driver.find_elements(By.CSS_SELECTOR, "button.action-button.call")
            if call_buttons and len(call_buttons) > 0:
                call_text = call_buttons[0].text
                # Extract number from text like "Call 20"
                match = re.search(r'CALL (\d+)', call_text)
                if match:
                    current_bet = float(match.group(1))
                else:
                    current_bet = 0
            else:
                # If no call button with amount, look for bet-to-call elements
                bet_to_call_elements = driver.find_elements(By.CLASS_NAME, "bet-to-call")
                if bet_to_call_elements:
                    current_bet_text = bet_to_call_elements[0].text
                    current_bet = float(re.search(r'\d+', current_bet_text).group())
                else:
                    current_bet = 0
        except Exception as e:
            print(f"Error getting current bet: {e}")
            current_bet = 0
        
        # Count active opponents and their stacks
        opponent_stacks = []
        active_players = driver.find_elements(By.CLASS_NAME, "table-player:not(.you-player)")
        num_opponents = 0
        
        for player in active_players:
            try:
                # Check if the player is active (has cards or has folded but still in the hand)
                has_cards = len(player.find_elements(By.CLASS_NAME, "table-player-cards")) > 0
                is_folded = 'folded' in player.get_attribute('class')
                
                if has_cards:
                    num_opponents += 1
                    stack_text = player.find_element(By.CLASS_NAME, "table-player-stack").text
                    stack = float(re.search(r'\d+', stack_text).group())
                    opponent_stacks.append(stack)
            except:
                pass
        
        # Print the extracted information for debugging
        print("My hand:", my_hand)
        print("Community cards:", community_cards)
        print("Pot size:", pot_size)
        print("Potential Current bet:", current_bet)
        print("My stack:", my_stack)
        print("Number of opponents:", num_opponents)
        print("Opponent stacks:", opponent_stacks)
        print("Total Betted:", previously_betted)
        print("\n\n\n\n")

        # Use the extracted data to calculate the best decision
        if my_hand and len(my_hand) == 2:  # Only make a decision if we have hole cards
            try:
                best_decision = calculate_best_decision(
                    my_hand,
                    community_cards,
                    num_opponents,
                    pot_size,
                    current_bet,
                    my_stack,
                    bet_amount,
                    opponent_stacks,
                    num_simulations=500  # Use fewer simulations for faster results
                )
            except:
                pass
            
            print("="*50)
            print(f"RECOMMENDED ACTION: {best_decision[0]}")
            print(f"Expected Value: {best_decision[1]:.2f}")
            print("="*50)
            
            # Look for buttons to click based on decision
            try:
                decision_action = best_decision[0].split()[0].lower()
                
                if decision_action == "fold":
                    fold_button = driver.find_element(By.CSS_SELECTOR, "button.action-button.fold")
                    print("Fold button found, would click in automated version")
                    # fold_button.click()
                    
                elif decision_action == "call" or decision_action == "check":
                    call_button = driver.find_element(By.CSS_SELECTOR, "button.action-button.call")
                    print("Call button found, would click in automated version")
                    # call_button.click()
                    
                elif decision_action == "raise" or decision_action == "bet":
                    # Get the raise amount
                    raise_amount = float(best_decision[0].split()[1])
                    raise_button = driver.find_element(By.CSS_SELECTOR, "button.action-button.raise")
                    print(f"Raise button found, would set amount to {raise_amount} and click in automated version")
                    # Set the raise value in the slider or input
                    # raise_button.click()
                    
                elif decision_action == "all-in":
                    all_in_button = driver.find_element(By.CSS_SELECTOR, "button.action-button.allin")
                    print("All-in button found, would click in automated version")
                    # all_in_button.click()
            except Exception as e:
                print(f"Error interacting with buttons: {e}")
        

    



scrape_pokernow("https://www.pokernow.club/games/pgllNVxLe3-9JWSTKvVUzp7Ol")