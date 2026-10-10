import sys

def check_braces(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    for i, ch in enumerate(content):
        if ch in '([{':
            stack.append((ch, i))
        elif ch in ')]}':
            if not stack:
                print(f"Unmatched closing {ch} at position {i}")
                # Show context
                start = max(0, i-20)
                end = min(len(content), i+20)
                context = content[start:end]
                print(f"Context: {repr(context)}")
                # Highlight the problematic character
                rel_pos = i - start
                print(f"Position {i} is at relative position {rel_pos} in context: {repr(context[:rel_pos])} >>{context[rel_pos]}<< {repr(context[rel_pos+1:])}")
                return False
            last, _ = stack.pop()
            if last != mapping[ch]:
                print(f"Mismatched {ch} at position {i}: expected {mapping[ch]} but found {last}")
                # Show context
                start = max(0, i-20)
                end = min(len(content), i+20)
                context = content[start:end]
                print(f"Context: {repr(context)}")
                # Highlight the problematic character
                rel_pos = i - start
                print(f"Position {i} is at relative position {rel_pos} in context: {repr(context[:rel_pos])} >>{context[rel_pos]}<< {repr(context[rel_pos+1:])}")
                return False
    if stack:
        print(f"Unmatched opening braces: {stack}")
        # Show the first unmatched opening brace
        ch, pos = stack[0]
        start = max(0, pos-20)
        end = min(len(content), pos+20)
        context = content[start:end]
        print(f"Context of first unmatched opening brace: {repr(context)}")
        rel_pos = pos - start
        print(f"Position {pos} is at relative position {rel_pos} in context: {repr(context[:rel_pos])} >>{context[rel_pos]}<< {repr(content[rel_pos+1:])}")
        return False
    return True

if __name__ == '__main__':
    if check_braces('app.js'):
        print("Braces, parentheses, and brackets are balanced.")
    else:
        print("There are mismatches.")
        sys.exit(1)
