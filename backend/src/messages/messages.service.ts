import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import {
  Message,
  MessageChannel,
  MessageDirection,
  MessageStatus,
} from './entities/message.entity';
import { SmtpAdapter } from './adapters/smtp.adapter';
import { TwilioAdapter } from './adapters/twilio.adapter';
import { MessageAdapter } from './interfaces/message-adapter.interface';

@Injectable()
export class MessagesService {
  constructor(
    @InjectRepository(Message)
    private messageRepository: Repository<Message>,
    private smtpAdapter: SmtpAdapter,
    private twilioAdapter: TwilioAdapter,
  ) {}

  private getAdapter(channel: MessageChannel): MessageAdapter {
    switch (channel) {
      case MessageChannel.EMAIL:
        return this.smtpAdapter;
      case MessageChannel.SMS:
      case MessageChannel.WHATSAPP:
        return this.twilioAdapter;
      default:
        throw new Error(`Unsupported channel: ${channel}`);
    }
  }

  async sendMessage(
    clientId: string,
    channel: MessageChannel,
    to: string,
    subject: string,
    body: string,
  ): Promise<Message> {
    const adapter = this.getAdapter(channel);

    // Create message record
    const message = this.messageRepository.create({
      clientId,
      channel,
      direction: MessageDirection.OUTBOUND,
      status: MessageStatus.PENDING,
      to,
      subject,
      body,
    });

    await this.messageRepository.save(message);

    // Send via adapter
    const result = await adapter.send({ to, subject, body });

    // Update message with result
    if (result.success) {
      message.status = MessageStatus.SENT;
      message.sentAt = new Date();
      message.metadata = { messageId: result.messageId };
    } else {
      message.status = MessageStatus.FAILED;
      message.failedAt = new Date();
      message.errorMessage = result.error;
    }

    return this.messageRepository.save(message);
  }

  async receiveMessage(
    channel: MessageChannel,
    payload: any,
  ): Promise<Message> {
    const adapter = this.getAdapter(channel);
    const parsed = await adapter.parseInbound(payload);

    // Find client by phone/email
    // For now, we'll store without client association
    // In production, you'd lookup the client by the 'from' field

    const message = this.messageRepository.create({
      channel,
      direction: MessageDirection.INBOUND,
      status: MessageStatus.RECEIVED,
      from: parsed.from,
      to: parsed.to,
      body: parsed.body,
      metadata: parsed.metadata,
    });

    return this.messageRepository.save(message);
  }

  async findByClient(clientId: string): Promise<Message[]> {
    return this.messageRepository.find({
      where: { clientId },
      order: { createdAt: 'DESC' },
    });
  }
}
