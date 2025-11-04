import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as nodemailer from 'nodemailer';
import {
  MessageAdapter,
  SendMessageDto,
} from '../interfaces/message-adapter.interface';

@Injectable()
export class SmtpAdapter implements MessageAdapter {
  private transporter: nodemailer.Transporter;

  constructor(private configService: ConfigService) {
    this.transporter = nodemailer.createTransport({
      host: this.configService.get('SMTP_HOST'),
      port: this.configService.get('SMTP_PORT'),
      secure: this.configService.get('SMTP_SECURE') === 'true',
      auth: this.configService.get('SMTP_USER')
        ? {
            user: this.configService.get('SMTP_USER'),
            pass: this.configService.get('SMTP_PASSWORD'),
          }
        : undefined,
    });
  }

  async send(dto: SendMessageDto): Promise<{
    success: boolean;
    messageId?: string;
    error?: string;
  }> {
    try {
      const info = await this.transporter.sendMail({
        from: dto.from || this.configService.get('SMTP_FROM'),
        to: dto.to,
        subject: dto.subject,
        text: dto.body,
        html: dto.body, // Can be enhanced to support HTML templates
      });

      return {
        success: true,
        messageId: info.messageId,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  }

  async parseInbound(payload: any): Promise<{
    from: string;
    to: string;
    body: string;
    metadata?: Record<string, any>;
  }> {
    // SMTP typically doesn't have inbound parsing in this manner
    // This would be implemented with IMAP or webhook-based email services
    throw new Error('SMTP adapter does not support inbound message parsing');
  }
}
