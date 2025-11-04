import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Workflow } from './entities/workflow.entity';
import {
  WorkflowRun,
  WorkflowRunStatus,
} from './entities/workflow-run.entity';
import { MessagesService } from '../messages/messages.service';
import { MessageChannel } from '../messages/entities/message.entity';

@Injectable()
export class WorkflowsService {
  constructor(
    @InjectRepository(Workflow)
    private workflowRepository: Repository<Workflow>,
    @InjectRepository(WorkflowRun)
    private workflowRunRepository: Repository<WorkflowRun>,
    private messagesService: MessagesService,
  ) {}

  /**
   * Trigger workflows based on an event
   * Example: triggerWorkflows('client.onboarded', { clientId: '123', email: 'test@example.com' })
   */
  async triggerWorkflows(
    triggerType: string,
    context: Record<string, any>,
  ): Promise<WorkflowRun[]> {
    // Find all active workflows with matching trigger
    const workflows = await this.workflowRepository.find({
      where: { isActive: true },
    });

    const matchingWorkflows = workflows.filter(
      (w) => w.definition.trigger.type === triggerType,
    );

    const runs: WorkflowRun[] = [];

    for (const workflow of matchingWorkflows) {
      const run = await this.executeWorkflow(workflow, context);
      runs.push(run);
    }

    return runs;
  }

  /**
   * Execute a single workflow
   */
  async executeWorkflow(
    workflow: Workflow,
    context: Record<string, any>,
  ): Promise<WorkflowRun> {
    // Create workflow run
    const run = this.workflowRunRepository.create({
      workflowId: workflow.id,
      status: WorkflowRunStatus.RUNNING,
      context,
      startedAt: new Date(),
    });

    await this.workflowRunRepository.save(run);

    try {
      const results = {};

      // Execute each action in sequence
      for (const action of workflow.definition.actions) {
        const result = await this.executeAction(action, context);
        results[action.type] = result;
      }

      // Mark as completed
      run.status = WorkflowRunStatus.COMPLETED;
      run.results = results;
      run.completedAt = new Date();
    } catch (error) {
      // Mark as failed
      run.status = WorkflowRunStatus.FAILED;
      run.errorMessage = error.message;
      run.completedAt = new Date();
    }

    return this.workflowRunRepository.save(run);
  }

  /**
   * Execute a single action
   */
  private async executeAction(
    action: { type: string; config: Record<string, any> },
    context: Record<string, any>,
  ): Promise<any> {
    switch (action.type) {
      case 'send_email':
        return this.executeSendEmail(action.config, context);

      case 'send_sms':
        return this.executeSendSms(action.config, context);

      case 'create_task':
        // Implement task creation logic
        return { success: true, message: 'Task creation not implemented' };

      default:
        throw new Error(`Unknown action type: ${action.type}`);
    }
  }

  /**
   * Send email action
   */
  private async executeSendEmail(
    config: Record<string, any>,
    context: Record<string, any>,
  ): Promise<any> {
    const to = this.interpolate(config.to, context);
    const subject = this.interpolate(config.subject, context);
    const body = this.interpolate(config.body, context);

    const message = await this.messagesService.sendMessage(
      context.clientId,
      MessageChannel.EMAIL,
      to,
      subject,
      body,
    );

    return { success: true, messageId: message.id };
  }

  /**
   * Send SMS action
   */
  private async executeSendSms(
    config: Record<string, any>,
    context: Record<string, any>,
  ): Promise<any> {
    const to = this.interpolate(config.to, context);
    const body = this.interpolate(config.body, context);

    const message = await this.messagesService.sendMessage(
      context.clientId,
      MessageChannel.SMS,
      to,
      null,
      body,
    );

    return { success: true, messageId: message.id };
  }

  /**
   * Simple template interpolation
   * Example: "Hello {{firstName}}" with context {firstName: 'John'} => "Hello John"
   */
  private interpolate(template: string, context: Record<string, any>): string {
    return template.replace(/\{\{(\w+)\}\}/g, (_, key) => context[key] || '');
  }

  async findAll(): Promise<Workflow[]> {
    return this.workflowRepository.find();
  }

  async findOne(id: string): Promise<Workflow> {
    return this.workflowRepository.findOne({ where: { id } });
  }

  async create(data: Partial<Workflow>): Promise<Workflow> {
    const workflow = this.workflowRepository.create(data);
    return this.workflowRepository.save(workflow);
  }
}
