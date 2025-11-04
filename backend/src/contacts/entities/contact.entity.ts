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

export enum ContactMethod {
  EMAIL = 'email',
  PHONE = 'phone',
  SMS = 'sms',
  WHATSAPP = 'whatsapp',
  IN_PERSON = 'in_person',
}

export enum ContactDirection {
  INBOUND = 'inbound',
  OUTBOUND = 'outbound',
}

@Entity('contacts')
export class Contact {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'client_id' })
  clientId: string;

  @ManyToOne(() => Client, (client) => client.contacts)
  @JoinColumn({ name: 'client_id' })
  client: Client;

  @Column({
    type: 'enum',
    enum: ContactMethod,
  })
  method: ContactMethod;

  @Column({
    type: 'enum',
    enum: ContactDirection,
  })
  direction: ContactDirection;

  @Column()
  subject: string;

  @Column({ type: 'text' })
  notes: string;

  @Column({ name: 'contacted_at' })
  contactedAt: Date;

  @Column({ name: 'contacted_by', nullable: true })
  contactedBy: string; // User ID

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;
}
