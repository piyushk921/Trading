import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { MessagesService } from './messages.service';
import { Message } from './entities/message.entity';
import { SmtpAdapter } from './adapters/smtp.adapter';
import { TwilioAdapter } from './adapters/twilio.adapter';

@Module({
  imports: [TypeOrmModule.forFeature([Message])],
  providers: [MessagesService, SmtpAdapter, TwilioAdapter],
  exports: [MessagesService],
})
export class MessagesModule {}
