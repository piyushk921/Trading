import { Controller, Post, Body, Headers } from '@nestjs/common';
import { MessagesService } from '../messages/messages.service';
import { MessageChannel } from '../messages/entities/message.entity';

@Controller('api/webhooks')
export class WebhooksController {
  constructor(private messagesService: MessagesService) {}

  @Post('twilio')
  async handleTwilioWebhook(
    @Body() payload: any,
    @Headers('x-twilio-signature') signature: string,
  ) {
    // In production, validate the webhook signature here
    // using TwilioAdapter.validateWebhookSignature()

    const channel = payload.To?.startsWith('whatsapp:')
      ? MessageChannel.WHATSAPP
      : MessageChannel.SMS;

    const message = await this.messagesService.receiveMessage(channel, payload);

    // Return TwiML response (optional)
    return {
      success: true,
      messageId: message.id,
    };
  }

  // Add more webhook handlers for other providers
  // @Post('whatsapp-business')
  // async handleWhatsAppBusinessWebhook() { ... }
}
