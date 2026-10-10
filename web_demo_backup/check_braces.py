import sys

def check_braces(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    # We'll ignore content inside strings and comments for simplicity, but for a quick check we can just count.
    # This is not perfect but can catch gross mismatches.
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    for i, ch in enumerate(content):
        if ch in '([{':
            stack.append((ch, i))
        elif ch in ')]}':
            if not stack:
                print(f"Unmatched closing {ch} at position {i}")
                return False
            last, _ = stack.pop()
            if mapping[ch] != last:
                print(f"Mismatched {ch} at position {i}: expected {mapping[ch]} but found {last}")
                return False
    if stack:
        print(f"Unmatched opening braces: {stack}")
        return False
    return True

if __name__ == '__main__':
    if check_braces('app.js'):
        print("Braces, parentheses, and brackets are balanced.")
    else:
        print("There are mismatches.")
        sys.exit(1)
