#!/usr/bin/env python3
"""
AES-GCM 完整示例：密码派生 + AEAD 加密与解密
"""

import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ==== 参数配置（最佳实践） ====
KEY_LENGTH = 32              # 256 位密钥
NONCE_LENGTH = 12            # 96 位随机 nonce（GCM 推荐）
SALT_LENGTH = 16             # 128 位随机 salt（KDF 用）
PBKDF2_ITERATIONS = 390_000  # 推荐的迭代次数（cryptography 默认值）
ASSOCIATED_DATA = "fileMetadata:data2025".encode('utf-8')
def _derive_key(salt: bytes) -> bytes:
    KEY_MATERIAL = "Str0ngP@ssw0rd!WE@R423><mnUbv%:{"
    """
    从用户密码派生 AES 密钥
    - 算法：PBKDF2-HMAC-SHA256
    - 输入：password、salt
    - 输出：固定长度 KEY_LENGTH 的密钥
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(KEY_MATERIAL.encode('utf-8'))

def encrypt(plain_text: str) -> str:
    """
    加密
    @param plain_text: 原文,需要加密的字符串
    """
    if not plain_text:
        raise ValueError("plain_text cannot be empty")

    salt = os.urandom(SALT_LENGTH)
    key = _derive_key(salt)
    astc = AESGCM(key)

    nonce = os.urandom(NONCE_LENGTH)
    ciphertext = astc.encrypt(nonce, plain_text.encode('utf-8'), ASSOCIATED_DATA)

    # 拼接：salt + nonce + 密文+tag，统一 Base64 编码
    data = salt + nonce + ciphertext
    return base64.b64encode(data).decode('utf-8')

def decrypt(cipher_text: str) -> str:
    """
    解密
    @param cipher_text: 密文,需要解密的字符串
    """
    if not cipher_text:
        raise ValueError("cipher_text cannot be empty")

    data = base64.b64decode(cipher_text)
    salt = data[:SALT_LENGTH]
    nonce = data[SALT_LENGTH:SALT_LENGTH + NONCE_LENGTH]
    ct_and_tag = data[SALT_LENGTH + NONCE_LENGTH:]

    key = _derive_key(salt)
    astc = AESGCM(key)
    return astc.decrypt(nonce, ct_and_tag, ASSOCIATED_DATA).decode('utf-8')


# ==== 示例用法 ====
if __name__ == "__main__":

    # 2. 要加密的明文数据 & 可选关联数据（例如报头、防篡改元信息）
    plaintext = "中文明文123456^&*()1111111111111111111111111111111111111111111111111111222222222223ddfdsfsdfsadfadfs"

    # 3. 加密
    encrypted_b64 = encrypt(plaintext)
    print("加密结果 (Base64)：", encrypted_b64)

    # 4. 解密
    decrypted = str(decrypt(encrypted_b64))
    print("解密后明文：", decrypted)
