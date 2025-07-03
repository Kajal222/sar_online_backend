import sys, json

def detect_paragraphs(text):
    paras = text.split('\n\n')
    formatted = []
    for idx, para in enumerate(paras):
        if para.strip():
            formatted.append(f"{idx+1}. {para.strip()}")
    return formatted

if __name__ == "__main__":
    text = open(sys.argv[1]).read()
    paragraphs = detect_paragraphs(text)
    print(json.dumps(paragraphs))
