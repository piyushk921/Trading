import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { Client } from '../../clients/entities/client.entity';

export enum DocumentType {
  PAN_CARD = 'pan_card',
  AADHAAR = 'aadhaar',
  BANK_STATEMENT = 'bank_statement',
  INVESTMENT_STATEMENT = 'investment_statement',
  KYC_DOCUMENT = 'kyc_document',
  CONTRACT = 'contract',
  OTHER = 'other',
}

@Entity('documents')
export class Document {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'client_id' })
  clientId: string;

  @ManyToOne(() => Client, (client) => client.documents)
  @JoinColumn({ name: 'client_id' })
  client: Client;

  @Column()
  name: string;

  @Column({
    type: 'enum',
    enum: DocumentType,
  })
  type: DocumentType;

  @Column({ name: 'file_path' })
  filePath: string; // Path to encrypted file on disk

  @Column({ name: 'file_size' })
  fileSize: number; // Size in bytes

  @Column({ name: 'mime_type' })
  mimeType: string;

  @Column({ name: 'uploaded_by', nullable: true })
  uploadedBy: string; // User ID

  @Column({ type: 'text', nullable: true })
  notes: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;
}
