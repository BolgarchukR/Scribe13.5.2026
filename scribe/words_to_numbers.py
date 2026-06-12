# words_to_numbers.py
import re
import logging

# Dictionaries mapping words to their numeric values
RU_NUMBERS = {
    # Units
    "ноль": 0, "нуль": 0, "ноля": 0, "нуля": 0,
    "один": 1, "одна": 1, "одно": 1, "одного": 1, "одному": 1, "одной": 1, "одну": 1, "одним": 1,
    "два": 2, "две": 2, "двух": 2, "двум": 2, "двумя": 2,
    "три": 3, "трех": 3, "трем": 3, "тремя": 3,
    "четыре": 4, "четырех": 4, "четырем": 4, "четырьмя": 4,
    "пять": 5, "пяти": 5, "пятью": 5,
    "шесть": 6, "весть": 6, "шести": 6, "шестью": 6,
    "семь": 7, "семи": 7, "семью": 7,
    "восемь": 8, "восьми": 8, "восемью": 8,
    "девять": 9, "девяти": 9, "девятью": 9,
    # Teens
    "десять": 10, "десяти": 10, "десятью": 10,
    "одиннадцать": 11, "одиннадцати": 11, "одиннадцатью": 11,
    "двенадцать": 12, "двенадцати": 12, "двенадцатью": 12,
    "тринадцать": 13, "тринадцати": 13, "тринадцатью": 13,
    "четырнадцать": 14, "четырнадцати": 14, "четырнадцатью": 14,
    "пятнадцать": 15, "пятнадцати": 15, "пятнадцатью": 15,
    "шестнадцать": 16, "шестнадцати": 16, "шестнадцатью": 16,
    "семнадцать": 17, "семнадцати": 17, "семнадцатью": 17,
    "восемнадцать": 18, "восемнадцати": 18, "восемнадцатью": 18,
    "девятнадцать": 19, "девятнадцати": 19, "девятнадцатью": 19,
    # Tens
    "двадцать": 20, "двадцати": 20, "двадцатью": 20,
    "тридцать": 30, "тридцати": 30, "тридцатью": 30,
    "сорок": 40, "сорока": 40,
    "пятьдесят": 50, "пятидесяти": 50, "пятьюдесятью": 50,
    "шестьдесят": 60, "шестидесяти": 60, "шестьюдесятью": 60,
    "семьдесят": 70, "семидесяти": 70, "семюдесятью": 70, "семьюдесятью": 70,
    "восемьдесят": 80, "восьмидесяти": 80, "восемьюдесятью": 80,
    "девяносто": 90, "девяноста": 90,
    # Hundreds
    "сто": 100, "ста": 100, "сот": 100,
    "двести": 200, "двухсот": 200, "двумстам": 200, "двумястами": 200, "двухстах": 200,
    "триста": 300, "трехсот": 300, "тремстам": 300, "тремястами": 300, "трехстах": 300,
    "четыреста": 400, "четырехсот": 400, "четыремстам": 400, "четырьмястами": 400, "четырехстах": 400,
    "пятьсот": 500, "пятисот": 500, "пятистам": 500, "пятьюстами": 500, "пятистах": 500,
    "шестьсот": 600, "шестисот": 600, "шестистам": 600, "шестьюстами": 600, "шестистах": 600,
    "семьсот": 700, "семисот": 700, "семистам": 700, "семьюстами": 700, "семистах": 700,
    "восемьсот": 800, "восьмисот": 800, "восьмистам": 800, "восемьюстами": 800, "восьмистах": 800,
    "девятьсот": 900, "девятисот": 900, "девятистам": 900, "девятьюстами": 900, "девятистах": 900,
}

UA_NUMBERS = {
    # Units
    "нуль": 0, "нуля": 0, "нулю": 0, "нулем": 0, "нулі": 0,
    "один": 1, "одна": 1, "одне": 1, "одного": 1, "одному": 1, "одній": 1, "одну": 1, "одні": 1, "одних": 1, "одним": 1, "одними": 1,
    "два": 2, "дві": 2, "двох": 2, "двом": 2, "двома": 2,
    "три": 3, "трьох": 3, "трьом": 3, "трьома": 3,
    "чотири": 4, "чотирьох": 4, "чотирьом": 4, "чотирма": 4,
    "п'ять": 5, "п’ять": 5, "п'яти": 5, "п’яти": 5, "п'ятьма": 5, "п’ятьма": 5, "п'ятьох": 5, "п’ятьох": 5, "п'ятьом": 5, "п’ятьом": 5,
    "шість": 6, "шести": 6, "шістьма": 6, "шістьох": 6, "шістьом": 6, "шістьома": 6,
    "сім": 7, "семи": 7, "сьома": 7, "сімох": 7, "сімом": 7, "сімома": 7,
    "вісім": 8, "восьми": 8, "вісьма": 8, "вісьмох": 8, "вісьмом": 8, "вісьмома": 8,
    "дев'ять": 9, "дев’ять": 9, "дев'яти": 9, "дев’яти": 9, "дев'ятьма": 9, "дев’ятьма": 9, "дев'ятьох": 9, "дев’ятьох": 9, "дев'ятьом": 9, "дев’ятьом": 9,
    # Teens
    "десять": 10, "десяти": 10, "десятьма": 10, "десятьох": 10, "десятьом": 10, "десятьома": 10,
    "одинадцять": 11, "одинадцяти": 11, "одинадцятьма": 11, "одинадцятьох": 11, "одинадцятьом": 11,
    "дванадцять": 12, "дванадцяти": 12, "дванадцятьма": 12, "дванадцятьох": 12, "дванадцятьом": 12,
    "тринадцять": 13, "тринадцяти": 13, "тринадцятьма": 13, "тринадцятьох": 13, "тринадцятьом": 13,
    "чотирнадцять": 14, "чотирнадцяти": 14, "чотирнадцятьма": 14, "чотирнадцятьох": 14, "чотирнадцятьом": 14,
    "п'ятнадцять": 15, "п’ятнадцять": 15, "п'ятнадцяти": 15, "п’ятнадцяти": 15, "п'ятнадцятьма": 15, "п’ятнадцятьма": 15, "п'ятнадцятьох": 15, "п’ятнадцятьох": 15,
    "шістнадцять": 16, "шістнадцяти": 16, "шістнадцятьма": 16, "шістнадцятьох": 16, "шістнадцятьом": 16,
    "сімнадцять": 17, "сімнадцяти": 17, "сімнадцятьма": 17, "сімнадцятьох": 17, "сімнадцятьом": 17,
    "вісімнадцять": 18, "вісімнадцяти": 18, "вісімнадцятьма": 18, "вісімнадцятьох": 18, "вісімнадцятьом": 18,
    "дев'ятнадцять": 19, "дев’ятнадцять": 19, "дев'ятнадцяти": 19, "дев’ятнадцяти": 19, "дев'ятнадцятьма": 19, "дев’ятнадцятьма": 19, "дев'ятнадцятьох": 19, "дев’ятнадцятьох": 19,
    # Tens
    "двадцять": 20, "двадцяти": 20, "двадцятьма": 20, "двадцятьох": 20, "двадцятьом": 20,
    "тридцять": 30, "тридцяти": 30, "тридцятьма": 30, "тридцятьох": 30, "тридцятьом": 30,
    "сорок": 40, "сорока": 40, "сорокам": 40, "сороками": 40, "сороках": 40,
    "п'ятдесят": 50, "п’ятдесят": 50, "п'ятдесяти": 50, "п’ятдесяти": 50, "п'ятдесятьма": 50, "п’ятдесятьма": 50, "п'ятдесятьох": 50, "п’ятдесятьох": 50,
    "шістдесят": 60, "шістдесяти": 60, "шістдесятьма": 60, "шістдесятьох": 60, "шістдесятком": 60,
    "сімдесят": 70, "сімдесяти": 70, "сімдесятьма": 70, "сімдесятьох": 70,
    "вісімдесят": 80, "вісімдесяти": 80, "вісімдесятьма": 80, "вісімдесятьох": 80,
    "дев'яносто": 90, "дев’яносто": 90, "дев'яноста": 90, "дев’яноста": 90,
    # Hundreds
    "сто": 100, "ста": 100, "стом": 100, "стами": 100, "стах": 100,
    "двісті": 200, "двохсот": 200, "двомстам": 200, "двомастами": 200, "двохстах": 200,
    "триста": 300, "трьохсот": 300, "трьомстам": 300, "трьомастами": 300, "трьохстах": 300,
    "чотириста": 400, "чотирьохсот": 400, "чотирьомстам": 400, "чотирмастами": 400, "чотирьохстах": 400,
    "п'ятсот": 500, "п’ятсот": 500, "п'ятисот": 500, "п’ятисот": 500, "п'ятистам": 500, "п’ятистам": 500, "п'ятсотма": 500, "п’ятсотма": 500,
    "шістсот": 600, "шестисот": 600, "шестистам": 600, "шістсотма": 600, "шістсотам": 600,
    "сімсот": 700, "семисот": 700, "семистам": 700, "сімсотма": 700,
    "вісімсот": 800, "восьмисот": 800, "восьмистам": 800, "вісімсотма": 800,
    "дев'ятсот": 900, "дев’ятсот": 900, "дев'ятисот": 900, "дев’ятисот": 900, "дев'ятистам": 900, "дев’ятистам": 900, "дев'ятсотма": 900,
}

EN_NUMBERS = {
    "zero": 0, "oh": 0, "nought": 0, "nil": 0,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

# Scale mappings
RU_SCALES = {
    "тысяча": 1000, "тысячи": 1000, "тысяче": 1000, "тысячей": 1000, "тысячу": 1000, "тысячам": 1000, "тысячами": 1000, "тысячах": 1000, "тысяч": 1000,
    "миллион": 1000000, "миллиона": 1000000, "миллиону": 1000000, "миллионом": 1000000, "миллионе": 1000000, "миллионы": 1000000, "миллионов": 1000000, "миллионам": 1000000, "миллионами": 1000000, "миллионах": 1000000,
    "миллиард": 1000000000, "миллиарда": 1000000000, "миллиарду": 1000000000, "миллиардом": 1000000000, "миллиарде": 1000000000, "миллиарды": 1000000000, "миллиардов": 1000000000, "миллиардам": 1000000000, "миллиардами": 1000000000, "миллиардах": 1000000000,
}

UA_SCALES = {
    "тисяча": 1000, "тисячі": 1000, "тисячею": 1000, "тисяч": 1000, "тисячам": 1000, "тисячами": 1000, "тисячах": 1000,
    "мільйон": 1000000, "мільйона": 1000000, "мільйону": 1000000, "мільйоном": 1000000, "мільйони": 1000000, "мільйонів": 1000000, "мільйонам": 1000000, "мільйонами": 1000000, "мільйонах": 1000000,
    "мільярд": 1000000000, "мільярда": 1000000000, "мільярду": 1000000000, "мільярдом": 1000000000, "мільярди": 1000000000, "мільярдів": 1000000000, "мільярдам": 1000000000, "мільярдами": 1000000000, "мільярдах": 1000000000,
}

EN_SCALES = {
    "hundred": 100,
    "thousand": 1000,
    "million": 1000000,
    "billion": 1000000000,
}

# Decimals separators
RU_DECIMAL_SEPS = {"целая", "целых", "целые", "целого", "целым", "целому"}
UA_DECIMAL_SEPS = {"ціла", "цілих", "цілі", "цілого", "цілому"}
EN_DECIMAL_SEPS = {"point", "dot"}

# Decimals multipliers
RU_DECIMAL_MULT = {
    "десятая": 0.1, "десятых": 0.1, "десятые": 0.1, "десятой": 0.1, "десятую": 0.1,
    "сотая": 0.01, "сотых": 0.01, "сотые": 0.01, "сотой": 0.01, "сотую": 0.01,
    "тысячная": 0.001, "тысячных": 0.001, "тысячные": 0.001, "тысячной": 0.001, "тысячную": 0.001,
}

UA_DECIMAL_MULT = {
    "десята": 0.1, "десятих": 0.1, "десяті": 0.1, "десятою": 0.1, "десяту": 0.1,
    "сота": 0.01, "сотих": 0.01, "соті": 0.01, "сотою": 0.01, "соту": 0.01,
    "тисячна": 0.001, "тисячних": 0.001, "тисячні": 0.001, "тисячною": 0.001, "тисячну": 0.001,
}

NUMBERS = {**RU_NUMBERS, **UA_NUMBERS, **EN_NUMBERS}
SCALES = {**RU_SCALES, **UA_SCALES, **EN_SCALES}
DECIMAL_SEPS = RU_DECIMAL_SEPS | UA_DECIMAL_SEPS | EN_DECIMAL_SEPS | {"точка", "запятая", "крапка", "кома"}
DECIMAL_MULTS = {**RU_DECIMAL_MULT, **UA_DECIMAL_MULT}

ALL_NUMBER_WORDS = (
    set(NUMBERS.keys())
    | set(SCALES.keys())
    | DECIMAL_SEPS
    | set(DECIMAL_MULTS.keys())
    | {"and"}
)

RU_UA_ONES = {"один", "одна", "одно", "одне", "одного", "одному", "одной", "одну", "одним", "одній"}

UNIT_STEMS = {
    # Russian
    "метр", "сантиметр", "миллиметр", "километр", "секунд", "минут", "час", "градус", "процент",
    "доллар", "евро", "рубл", "гривн", "копейк", "цент", "литр", "миллилитр", "килограм",
    "грамм", "миллиграм", "тонн", "шаг", "день", "раз", "класс", "этаж",
    # Ukrainian
    "хвилин", "годин", "літр", "мілілітр", "кілометр", "міліметр", "кілограм", "грам", "тонн",
    # English
    "meter", "centimeter", "millimeter", "kilometer", "second", "minute", "hour", "percent",
    "degree", "dollar", "euro", "pound",
    # Standard Abbreviations (RU/UA/EN)
    "см", "мм", "км", "м", "кг", "г", "мг", "т", "сек", "мин", "ч", "л", "мл", "грн", "руб", "хв", "год", "$", "€", "°", "%",
    "cm", "cm", "mm", "m", "km", "kg", "g", "sec", "min", "hr"
}

def get_number_category(val):
    if val >= 100 and val < 1000:
        return 4  # Hundreds
    elif val in {10, 20, 30, 40, 50, 60, 70, 80, 90}:
        return 3  # Tens
    elif val >= 11 and val <= 19:
        return 2  # Teens
    elif val >= 0 and val <= 9:
        return 1  # Units
    return 0

def parse_int_words(words):
    if not words:
        return None

    total = 0
    current = 0
    prev_scale = 9999999999999
    prev_cat = 5  # Category higher than Hundreds (4)

    # If the list is just a single scale word, like ["тысяча"], it should parse as 1000
    if len(words) == 1 and words[0] in SCALES:
        return SCALES[words[0]]

    for w in words:
        if w in SCALES:
            scale = SCALES[w]
            if scale >= prev_scale:
                return None
            mult = current if current != 0 else 1
            total += mult * scale
            current = 0
            prev_scale = scale
            prev_cat = 5  # Reset category order for the next scale part
        elif w in NUMBERS:
            val = NUMBERS[w]
            cat = get_number_category(val)

            # Strict category order rules:
            # 1. New category must be strictly less than previous category
            # 2. If previous category was Tens (3), next cannot be Teens (2)
            if cat >= prev_cat:
                return None
            if prev_cat == 3 and cat == 2:
                return None

            current += val
            prev_cat = cat
        else:
            return None

    return total + current

def parse_words_to_number(words):
    if not words:
        return None

    # Check for decimal separator
    sep_idx = -1
    for i, w in enumerate(words):
        if w in DECIMAL_SEPS:
            sep_idx = i
            break

    if sep_idx != -1:
        int_words = words[:sep_idx]
        frac_words = words[sep_idx + 1:]
    else:
        int_words = words
        frac_words = []

    # Parse integer part
    int_val = parse_int_words(int_words)
    if int_val is None:
        return None

    if frac_words:
        # Check if the last word is a decimal multiplier (e.g. "десятых")
        multiplier = 1.0
        if frac_words[-1] in DECIMAL_MULTS:
            multiplier = DECIMAL_MULTS[frac_words[-1]]
            frac_words = frac_words[:-1]
            if frac_words:
                frac_val = parse_int_words(frac_words)
                if frac_val is None:
                    return None
            else:
                frac_val = 1
            frac_part = frac_val * multiplier
        else:
            # Direct/English: "point five" or "point zero five"
            all_single_digits = True
            digit_str = ""
            for w in frac_words:
                val = NUMBERS.get(w)
                if val is not None and val < 10:
                    digit_str += str(val)
                else:
                    all_single_digits = False
                    break

            if all_single_digits and digit_str:
                frac_part = float("0." + digit_str)
            else:
                # Compound like "point twenty five"
                frac_val = parse_int_words(frac_words)
                if frac_val is not None:
                    frac_part = frac_val / (10 ** len(str(frac_val)))
                else:
                    return None
        total_val = int_val + frac_part
    else:
        total_val = int_val

    # Suggest decimal separator (RU/UA use comma, EN uses dot)
    has_ru_ua = False
    for w in words:
        if (
            w in RU_NUMBERS
            or w in RU_SCALES
            or w in RU_DECIMAL_SEPS
            or w in RU_DECIMAL_MULT
            or w in UA_NUMBERS
            or w in UA_SCALES
            or w in UA_DECIMAL_SEPS
            or w in UA_DECIMAL_MULT
            or w in {"точка", "запятая", "крапка", "кома"}
        ):
            has_ru_ua = True
            break

    sep = ',' if has_ru_ua else '.'
    return total_val, sep

def tokenize(text):
    # Regex split pattern for alphanumeric word sequences, spaces, and punctuation
    pattern = re.compile(r"([a-zA-Zа-яА-ЯёЁіІїЇєЄґҐ\’\']+|\s+|[^\w\s])")
    tokens = [t for t in pattern.findall(text) if t]
    return tokens

def replace_numbers_in_text(text):
    if not text:
        return text

    tokens = tokenize(text)
    n = len(tokens)
    i = 0
    new_tokens = []

    while i < n:
        token_clean = tokens[i].lower().strip().replace("’", "'")
        is_num_word = token_clean in ALL_NUMBER_WORDS

        if not is_num_word:
            new_tokens.append(tokens[i])
            i += 1
            continue

        # Found a potential start of a number block. Search for the longest valid block tokens[i:j].
        longest_j = -1
        longest_num_str = None

        for j in range(n, i, -1):
            # Check for the last word index in block
            last_word_idx = -1
            for k in range(j - 1, i - 1, -1):
                tk_clean = tokens[k].lower().strip().replace("’", "'")
                if tk_clean and (tk_clean.isalnum() or "'" in tk_clean):
                    last_word_idx = k
                    break

            if last_word_idx == -1:
                continue

            # Validate that all tokens between i and last_word_idx are number words or spaces/hyphens
            valid_block = True
            words = []
            for k in range(i, last_word_idx + 1):
                tk = tokens[k]
                tk_clean = tk.lower().strip().replace("’", "'")
                if tk_clean and (tk_clean.isalnum() or "'" in tk_clean):
                    if tk_clean in ALL_NUMBER_WORDS or tk_clean == "and":
                        words.append(tk_clean)
                    else:
                        valid_block = False
                        break
                else:
                    if tk.strip() and tk != '-':
                        valid_block = False
                        break

            if not valid_block:
                continue

            # Try parsing the clean words sequence (ignoring English "and")
            parse_words = [w for w in words if w != "and"]
            res = parse_words_to_number(parse_words)
            if res is not None:
                val, sep = res
                if val == int(val):
                    num_str = str(int(val))
                else:
                    num_str = f"{val:.15g}".replace('.', sep)
                longest_j = last_word_idx + 1
                longest_num_str = num_str
                break

        if longest_j != -1:
            # Check if this is a single "one" word
            is_single_one = False
            block_words = []
            for k in range(i, longest_j):
                tk_clean = tokens[k].lower().strip().replace("’", "'")
                if tk_clean and (tk_clean.isalnum() or "'" in tk_clean):
                    block_words.append(tk_clean)
            
            if len(block_words) == 1 and block_words[0] in RU_UA_ONES:
                is_single_one = True
                
            if is_single_one:
                next_word = None
                for k in range(longest_j, n):
                    tk_clean = tokens[k].lower().strip().replace("’", "'")
                    if tk_clean and (tk_clean.isalnum() or "'" in tk_clean):
                        next_word = tk_clean
                        break
                
                has_unit = False
                if next_word:
                    if next_word in ALL_NUMBER_WORDS:
                        has_unit = True
                    else:
                        for stem in UNIT_STEMS:
                            if next_word.startswith(stem):
                                has_unit = True
                                break
                            
                if not has_unit:
                    new_tokens.append(tokens[i])
                    i += 1
                    continue
            
            new_tokens.append(longest_num_str)
            logger = logging.getLogger(__name__)
            logger.info(f"[COMMAND] Hit: Number Conversion | Param: {longest_num_str}")
            i = longest_j
        else:
            new_tokens.append(tokens[i])
            i += 1

    return "".join(new_tokens)
