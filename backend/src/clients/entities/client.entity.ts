import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { Contact } from '../../contacts/entities/contact.entity';
import { Message } from '../../messages/entities/message.entity';
import { Task } from '../../tasks/entities/task.entity';
import { Document } from '../../documents/entities/document.entity';
import { Consent } from './consent.entity';
import { PortfolioLink } from './portfolio-link.entity';
import { User } from '../../users/entities/user.entity';

export enum ClientStatus {
  PROSPECT = 'prospect',
  ONBOARDING = 'onboarding',
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  CHURNED = 'churned',
}

export enum RiskProfile {
  CONSERVATIVE = 'conservative',
  MODERATE = 'moderate',
  AGGRESSIVE = 'aggressive',
}

@Entity('clients')
export class Client {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'first_name' })
  firstName: string;

  @Column({ name: 'last_name' })
  lastName: string;

  @Column({ unique: true })
  email: string;

  @Column({ nullable: true })
  phone: string;

  @Column({ nullable: true, name: 'alternate_phone' })
  alternatePhone: string;

  // ENCRYPTED FIELD: PAN (Personal Account Number)
  // Uses pgcrypto extension with ENCRYPTION_KEY from environment
  @Column({ type: 'bytea', nullable: true })
  pan: Buffer;

  // ENCRYPTED FIELD: Bank Account Number
  @Column({ type: 'bytea', nullable: true, name: 'bank_account' })
  bankAccount: Buffer;

  @Column({ nullable: true, name: 'bank_name' })
  bankName: string;

  @Column({ nullable: true, name: 'bank_ifsc' })
  bankIfsc: string;

  @Column({ type: 'text', nullable: true })
  address: string;

  @Column({ nullable: true })
  city: string;

  @Column({ nullable: true })
  state: string;

  @Column({ nullable: true, name: 'postal_code' })
  postalCode: string;

  @Column({ nullable: true })
  country: string;

  @Column({ nullable: true, name: 'date_of_birth' })
  dateOfBirth: Date;

  @Column({
    type: 'enum',
    enum: ClientStatus,
    default: ClientStatus.PROSPECT,
  })
  status: ClientStatus;

  @Column({
    type: 'enum',
    enum: RiskProfile,
    nullable: true,
    name: 'risk_profile',
  })
  riskProfile: RiskProfile;

  @Column({ nullable: true, name: 'assigned_rm_id' })
  assignedRmId: string;

  @ManyToOne(() => User, { nullable: true })
  @JoinColumn({ name: 'assigned_rm_id' })
  assignedRm: User;

  @Column({ type: 'boolean', default: false, name: 'is_onboarded' })
  isOnboarded: boolean;

  @Column({ nullable: true, name: 'onboarded_at' })
  onboardedAt: Date;

  @Column({ type: 'text', nullable: true })
  notes: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  @OneToMany(() => Contact, (contact) => contact.client)
  contacts: Contact[];

  @OneToMany(() => Message, (message) => message.client)
  messages: Message[];

  @OneToMany(() => Task, (task) => task.client)
  tasks: Task[];

  @OneToMany(() => Document, (document) => document.client)
  documents: Document[];

  @OneToMany(() => Consent, (consent) => consent.client)
  consents: Consent[];

  @OneToMany(() => PortfolioLink, (link) => link.client)
  portfolioLinks: PortfolioLink[];
}
