import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { AuditLog, AuditAction } from '../../audit/entities/audit-log.entity';

@Injectable()
export class AuditLogInterceptor implements NestInterceptor {
  constructor(
    @InjectRepository(AuditLog)
    private auditLogRepository: Repository<AuditLog>,
  ) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { user, method, url, ip, body } = request;

    // Map HTTP methods to audit actions
    const actionMap: Record<string, AuditAction> = {
      POST: AuditAction.CREATE,
      PUT: AuditAction.UPDATE,
      PATCH: AuditAction.UPDATE,
      DELETE: AuditAction.DELETE,
    };

    const action = actionMap[method];

    // Only log CUD operations (not READ)
    if (!action) {
      return next.handle();
    }

    return next.handle().pipe(
      tap(async (data) => {
        try {
          // Extract entity info from URL
          const urlParts = url.split('/').filter(Boolean);
          const entityType = urlParts[urlParts.length - 2] || 'unknown';
          const entityId = data?.id || body?.id || null;

          await this.auditLogRepository.save({
            userId: user?.userId || null,
            action,
            entityType,
            entityId,
            changes: { body, response: data },
            ipAddress: ip,
            userAgent: request.get('user-agent'),
          });
        } catch (error) {
          // Don't fail the request if audit logging fails
          console.error('Audit logging failed:', error);
        }
      }),
    );
  }
}
