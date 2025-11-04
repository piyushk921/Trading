import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
} from 'typeorm';
import { WorkflowRun } from './workflow-run.entity';

@Entity('workflows')
export class Workflow {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  name: string;

  @Column({ type: 'text', nullable: true })
  description: string;

  @Column({ type: 'jsonb' })
  definition: {
    trigger: {
      type: string; // e.g., 'client.onboarded', 'task.completed'
      conditions?: Record<string, any>;
    };
    actions: Array<{
      type: string; // e.g., 'send_email', 'create_task', 'send_sms'
      config: Record<string, any>;
    }>;
  };

  @Column({ type: 'boolean', default: true, name: 'is_active' })
  isActive: boolean;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  @OneToMany(() => WorkflowRun, (run) => run.workflow)
  runs: WorkflowRun[];
}
