def check_password(password, mod_divisor=10)-> bool:
    """
    Проверка пароля старост
    """
    main_part = password[:-1]  # Основная часть пароля (без контрольной цифры)
    checksum = int(password[-1])  # Контрольная цифра пароля
    calculated_checksum = sum(ord(c) for c in main_part) % mod_divisor
    return checksum == calculated_checksum

