export interface SendMessageDto {
  to: string;
  subject?: string;
  body: string;
  from?: string;
  metadata?: Record<string, any>;
}

export interface MessageAdapter {
  send(dto: SendMessageDto): Promise<{
    success: boolean;
    messageId?: string;
    error?: string;
  }>;

  parseInbound(payload: any): Promise<{
    from: string;
    to: string;
    body: string;
    metadata?: Record<string, any>;
  }>;
}
