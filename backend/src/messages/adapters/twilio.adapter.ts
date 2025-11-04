import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import {
  MessageAdapter,
  SendMessageDto,
} from '../interfaces/message-adapter.interface';

/**
 * Twilio SMS/WhatsApp Adapter
 *
 * This is a stub implementation that provides the interface for Twilio integration.
 * To enable actual sending:
 * 1. Uncomment the Twilio client import and initialization
 * 2. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env
 * 3. Ensure the phone numbers are in E.164 format (+1234567890)
 *
 * For WhatsApp:
 * - Prefix the phone number with 'whatsapp:' (e.g., 'whatsapp:+1234567890')
 * - Requires Twilio WhatsApp sandbox or approved sender
 */

// Uncomment for production use:
// import * as twilio from 'twilio';

@Injectable()
export class TwilioAdapter implements MessageAdapter {
  // private client: twilio.Twilio;
  private accountSid: string;
  private authToken: string;
  private fromNumber: string;

  constructor(private configService: ConfigService) {
    this.accountSid = this.configService.get('TWILIO_ACCOUNT_SID');
    this.authToken = this.configService.get('TWILIO_AUTH_TOKEN');
    this.fromNumber = this.configService.get('TWILIO_PHONE_NUMBER');

    // Uncomment for production use:
    // if (this.accountSid && this.authToken) {
    //   this.client = twilio(this.accountSid, this.authToken);
    // }
  }

  async send(dto: SendMessageDto): Promise<{
    success: boolean;
    messageId?: string;
    error?: string;
  }> {
    try {
      // STUB: Return success without actually sending
      console.log('[Twilio Stub] Would send message:', {
        from: dto.from || this.fromNumber,
        to: dto.to,
        body: dto.body,
      });

      // Uncomment for production use:
      // if (!this.client) {
      //   throw new Error('Twilio client not configured');
      // }
      //
      // const message = await this.client.messages.create({
      //   from: dto.from || this.fromNumber,
      //   to: dto.to,
      //   body: dto.body,
      // });
      //
      // return {
      //   success: true,
      //   messageId: message.sid,
      // };

      return {
        success: true,
        messageId: `stub_${Date.now()}`,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * Parse inbound Twilio webhook payload
   * Webhook URL: POST /api/webhooks/twilio
   */
  async parseInbound(payload: any): Promise<{
    from: string;
    to: string;
    body: string;
    metadata?: Record<string, any>;
  }> {
    return {
      from: payload.From,
      to: payload.To,
      body: payload.Body,
      metadata: {
        messageSid: payload.MessageSid,
        accountSid: payload.AccountSid,
        numMedia: payload.NumMedia,
        mediaUrls: payload.MediaUrl0 ? [payload.MediaUrl0] : [],
      },
    };
  }

  /**
   * Validate Twilio webhook signature
   * Use this in the webhook controller to ensure requests are from Twilio
   */
  validateWebhookSignature(
    signature: string,
    url: string,
    params: Record<string, any>,
  ): boolean {
    // Uncomment for production use:
    // const webhookSecret = this.configService.get('TWILIO_WEBHOOK_SECRET');
    // return twilio.validateRequest(webhookSecret, signature, url, params);

    // STUB: Always return true in development
    console.log('[Twilio Stub] Webhook signature validation bypassed');
    return true;
  }
}
