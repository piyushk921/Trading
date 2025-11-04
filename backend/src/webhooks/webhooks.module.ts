import { Module } from '@nestjs/common';
import { WebhooksController } from './webhooks.controller';
import { MessagesModule } from '../messages/messages.module';

@Module({
  imports: [MessagesModule],
  controllers: [WebhooksController],
})
export class WebhooksModule {}
