"""
Number to words conversion for Indian currency
"""
def number_to_words(num):
    """
    Convert number to words in Indian format
    Example: 4576 -> "Four Thousand Five Hundred and Seventy Six Rupees Only"
    """
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    def convert_less_than_thousand(n):
        if n == 0:
            return ""
        elif n < 20:
            return ones[n]
        elif n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
        else:
            return ones[n // 100] + " Hundred" + (" and " + convert_less_than_thousand(n % 100) if n % 100 != 0 else "")
    
    if num == 0:
        return "Zero Rupees Only"
    
    # Handle decimal part
    integer_part = int(num)
    decimal_part = round((num - integer_part) * 100)
    
    if integer_part == 0:
        result = "Zero"
    elif integer_part < 1000:
        result = convert_less_than_thousand(integer_part)
    elif integer_part < 100000:
        result = convert_less_than_thousand(integer_part // 1000) + " Thousand"
        if integer_part % 1000 != 0:
            result += " " + convert_less_than_thousand(integer_part % 1000)
    elif integer_part < 10000000:
        result = convert_less_than_thousand(integer_part // 100000) + " Lakh"
        remainder = integer_part % 100000
        if remainder != 0:
            if remainder < 1000:
                result += " " + convert_less_than_thousand(remainder)
            else:
                result += " " + convert_less_than_thousand(remainder // 1000) + " Thousand"
                if remainder % 1000 != 0:
                    result += " " + convert_less_than_thousand(remainder % 1000)
    else:
        result = convert_less_than_thousand(integer_part // 10000000) + " Crore"
        remainder = integer_part % 10000000
        if remainder != 0:
            if remainder < 100000:
                result += " " + convert_less_than_thousand(remainder)
            else:
                result += " " + convert_less_than_thousand(remainder // 100000) + " Lakh"
                remainder = remainder % 100000
                if remainder != 0:
                    if remainder < 1000:
                        result += " " + convert_less_than_thousand(remainder)
                    else:
                        result += " " + convert_less_than_thousand(remainder // 1000) + " Thousand"
                        if remainder % 1000 != 0:
                            result += " " + convert_less_than_thousand(remainder % 1000)
    
    result += " Rupees"
    
    if decimal_part > 0:
        result += " and " + convert_less_than_thousand(decimal_part) + " Paise"
    
    result += " Only"
    
    return result

