import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { Client } from './client.entity';

@Entity('portfolio_links')
export class PortfolioLink {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'client_id' })
  clientId: string;

  @ManyToOne(() => Client, (client) => client.portfolioLinks)
  @JoinColumn({ name: 'client_id' })
  client: Client;

  @Column({ name: 'external_portfolio_id' })
  externalPortfolioId: string; // ID in external portfolio management system

  @Column({ name: 'platform_name' })
  platformName: string; // e.g., 'Zerodha', 'Groww', 'Internal System'

  @Column({ type: 'jsonb', nullable: true })
  metadata: Record<string, any>; // Additional platform-specific data

  @Column({ type: 'boolean', default: true, name: 'is_active' })
  isActive: boolean;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;
}
