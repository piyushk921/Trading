import { createCipheriv, createDecipheriv, randomBytes } from 'crypto';

/**
 * Encryption utility for sensitive data (PII).
 *
 * IMPORTANT: The ENCRYPTION_KEY must be:
 * - 32 bytes (64 hex characters) for AES-256
 * - Stored securely (e.g., HashiCorp Vault, AWS Secrets Manager)
 * - Never committed to version control
 * - Rotated periodically with a key rotation strategy
 *
 * Key Management Recommendations:
 * 1. Development: Use .env file (never commit)
 * 2. Production: Use a secrets management system (Vault, AWS Secrets Manager, etc.)
 * 3. Implement key rotation with versioning
 * 4. Keep backup of old keys for decryption during rotation
 */

const ALGORITHM = 'aes-256-cbc';
const IV_LENGTH = 16; // For AES, this is always 16

export class EncryptionUtil {
  private static getKey(): Buffer {
    const key = process.env.ENCRYPTION_KEY;
    if (!key || key.length !== 64) {
      throw new Error(
        'ENCRYPTION_KEY must be set and be 64 hex characters (32 bytes) long',
      );
    }
    return Buffer.from(key, 'hex');
  }

  /**
   * Encrypts plaintext data
   * @param text - Plaintext to encrypt
   * @returns Buffer containing IV + encrypted data
   */
  static encrypt(text: string): Buffer {
    if (!text) return null;

    const iv = randomBytes(IV_LENGTH);
    const cipher = createCipheriv(ALGORITHM, this.getKey(), iv);

    const encrypted = Buffer.concat([
      cipher.update(text, 'utf8'),
      cipher.final(),
    ]);

    // Prepend IV to encrypted data
    return Buffer.concat([iv, encrypted]);
  }

  /**
   * Decrypts encrypted data
   * @param buffer - Buffer containing IV + encrypted data
   * @returns Decrypted plaintext
   */
  static decrypt(buffer: Buffer): string {
    if (!buffer) return null;

    // Extract IV from the beginning
    const iv = buffer.slice(0, IV_LENGTH);
    const encrypted = buffer.slice(IV_LENGTH);

    const decipher = createDecipheriv(ALGORITHM, this.getKey(), iv);

    const decrypted = Buffer.concat([
      decipher.update(encrypted),
      decipher.final(),
    ]);

    return decrypted.toString('utf8');
  }

  /**
   * For use with TypeORM transformers - encrypts on save
   */
  static encryptTransformer = {
    to: (value: string): Buffer => {
      return value ? EncryptionUtil.encrypt(value) : null;
    },
    from: (value: Buffer): string => {
      return value ? EncryptionUtil.decrypt(value) : null;
    },
  };
}

/**
 * Example usage with TypeORM entity:
 *
 * @Column({
 *   type: 'bytea',
 *   transformer: EncryptionUtil.encryptTransformer,
 * })
 * pan: string;
 *
 * This will automatically encrypt when saving and decrypt when loading.
 */
