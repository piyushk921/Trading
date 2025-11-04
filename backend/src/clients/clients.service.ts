import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Client, ClientStatus } from './entities/client.entity';
import { EncryptionUtil } from '../common/utils/encryption.util';
import { WorkflowsService } from '../workflows/workflows.service';

@Injectable()
export class ClientsService {
  constructor(
    @InjectRepository(Client)
    private clientRepository: Repository<Client>,
    private workflowsService: WorkflowsService,
  ) {}

  async create(data: Partial<Client>): Promise<Client> {
    // Encrypt sensitive fields before saving
    if (data.pan) {
      data.pan = EncryptionUtil.encrypt(data.pan as any) as any;
    }
    if (data.bankAccount) {
      data.bankAccount = EncryptionUtil.encrypt(data.bankAccount as any) as any;
    }

    const client = this.clientRepository.create(data);
    const saved = await this.clientRepository.save(client);

    // Trigger workflow if client is onboarded
    if (data.isOnboarded) {
      await this.workflowsService.triggerWorkflows('client.onboarded', {
        clientId: saved.id,
        email: saved.email,
        firstName: saved.firstName,
        lastName: saved.lastName,
      });
    }

    return this.findOne(saved.id);
  }

  async findAll(): Promise<Client[]> {
    const clients = await this.clientRepository.find({
      relations: ['assignedRm'],
    });

    // Decrypt sensitive fields
    return clients.map((client) => this.decryptClientFields(client));
  }

  async findOne(id: string): Promise<Client> {
    const client = await this.clientRepository.findOne({
      where: { id },
      relations: ['assignedRm', 'consents', 'portfolioLinks'],
    });

    if (!client) {
      throw new NotFoundException(`Client with ID ${id} not found`);
    }

    return this.decryptClientFields(client);
  }

  async update(id: string, data: Partial<Client>): Promise<Client> {
    const client = await this.findOne(id);

    // Encrypt sensitive fields
    if (data.pan) {
      data.pan = EncryptionUtil.encrypt(data.pan as any) as any;
    }
    if (data.bankAccount) {
      data.bankAccount = EncryptionUtil.encrypt(data.bankAccount as any) as any;
    }

    // Check if client is being marked as onboarded
    const wasOnboarded = client.isOnboarded;
    const isNowOnboarded = data.isOnboarded === true;

    await this.clientRepository.update(id, data);

    const updated = await this.findOne(id);

    // Trigger onboarding workflow if status changed
    if (!wasOnboarded && isNowOnboarded) {
      await this.workflowsService.triggerWorkflows('client.onboarded', {
        clientId: updated.id,
        email: updated.email,
        firstName: updated.firstName,
        lastName: updated.lastName,
      });
    }

    return updated;
  }

  async remove(id: string): Promise<void> {
    await this.findOne(id); // Ensure exists
    await this.clientRepository.delete(id);
  }

  private decryptClientFields(client: Client): Client {
    if (client.pan) {
      try {
        client.pan = EncryptionUtil.decrypt(client.pan as any) as any;
      } catch (error) {
        console.error('Failed to decrypt PAN:', error);
        client.pan = null;
      }
    }

    if (client.bankAccount) {
      try {
        client.bankAccount = EncryptionUtil.decrypt(
          client.bankAccount as any,
        ) as any;
      } catch (error) {
        console.error('Failed to decrypt bank account:', error);
        client.bankAccount = null;
      }
    }

    return client;
  }
}
