import { AppDataSource } from '../../config/typeorm.config';
import { Role, RoleName } from '../../users/entities/role.entity';
import { User, UserStatus } from '../../users/entities/user.entity';
import { Client, ClientStatus, RiskProfile } from '../../clients/entities/client.entity';
import { Workflow } from '../../workflows/entities/workflow.entity';
import * as argon2 from 'argon2';
import { EncryptionUtil } from '../../common/utils/encryption.util';

async function seed() {
  console.log('🌱 Starting database seed...');

  await AppDataSource.initialize();

  const roleRepository = AppDataSource.getRepository(Role);
  const userRepository = AppDataSource.getRepository(User);
  const clientRepository = AppDataSource.getRepository(Client);
  const workflowRepository = AppDataSource.getRepository(Workflow);

  // Create Roles
  console.log('Creating roles...');
  const roles = await Promise.all([
    roleRepository.save({
      name: RoleName.SUPER_ADMIN,
      description: 'Super Administrator with full access',
      permissions: { all: true },
    }),
    roleRepository.save({
      name: RoleName.ADMIN,
      description: 'Administrator with management access',
      permissions: { manageUsers: true, manageClients: true },
    }),
    roleRepository.save({
      name: RoleName.RM,
      description: 'Relationship Manager',
      permissions: { viewClients: true, createClients: true, editClients: true },
    }),
    roleRepository.save({
      name: RoleName.COMPLIANCE,
      description: 'Compliance Officer',
      permissions: { viewClients: true, viewAuditLogs: true },
    }),
  ]);

  const adminRole = roles.find((r) => r.name === RoleName.ADMIN);

  // Create Admin User
  console.log('Creating admin user...');
  const hashedPassword = await argon2.hash('ChangeMe123!');
  const adminUser = await userRepository.save({
    email: 'admin@benefactor.local',
    password: hashedPassword,
    firstName: 'Admin',
    lastName: 'User',
    status: UserStatus.ACTIVE,
    roleId: adminRole.id,
  });

  // Create Demo Clients
  console.log('Creating demo clients...');
  await clientRepository.save([
    {
      firstName: 'Rajesh',
      lastName: 'Kumar',
      email: 'rajesh.kumar@example.com',
      phone: '+919876543210',
      pan: EncryptionUtil.encrypt('ABCDE1234F'),
      bankAccount: EncryptionUtil.encrypt('1234567890'),
      bankName: 'HDFC Bank',
      bankIfsc: 'HDFC0001234',
      address: '123 MG Road',
      city: 'Mumbai',
      state: 'Maharashtra',
      postalCode: '400001',
      country: 'India',
      dateOfBirth: new Date('1985-05-15'),
      status: ClientStatus.ACTIVE,
      riskProfile: RiskProfile.MODERATE,
      assignedRmId: adminUser.id,
      isOnboarded: true,
      onboardedAt: new Date(),
      notes: 'High net-worth individual interested in equity investments',
    },
    {
      firstName: 'Priya',
      lastName: 'Sharma',
      email: 'priya.sharma@example.com',
      phone: '+919123456780',
      pan: EncryptionUtil.encrypt('XYZAB5678C'),
      bankAccount: EncryptionUtil.encrypt('9876543210'),
      bankName: 'ICICI Bank',
      bankIfsc: 'ICIC0004567',
      address: '456 Park Street',
      city: 'Bangalore',
      state: 'Karnataka',
      postalCode: '560001',
      country: 'India',
      dateOfBirth: new Date('1990-08-22'),
      status: ClientStatus.ONBOARDING,
      riskProfile: RiskProfile.CONSERVATIVE,
      assignedRmId: adminUser.id,
      isOnboarded: false,
      notes: 'New client, completing KYC process',
    },
  ]);

  // Create Welcome Email Workflow
  console.log('Creating workflows...');
  await workflowRepository.save({
    name: 'Welcome Email on Onboarding',
    description: 'Automatically send welcome email when client is onboarded',
    definition: {
      trigger: {
        type: 'client.onboarded',
      },
      actions: [
        {
          type: 'send_email',
          config: {
            to: '{{email}}',
            subject: 'Welcome to Benefactor Wealth',
            body: `Dear {{firstName}} {{lastName}},

Welcome to Benefactor Wealth! We're excited to have you as a client.

Your account has been successfully set up, and your dedicated Relationship Manager will be in touch with you shortly to discuss your investment goals and financial planning.

If you have any questions, please don't hesitate to reach out.

Best regards,
The Benefactor Wealth Team`,
          },
        },
      ],
    },
    isActive: true,
  });

  console.log('✅ Seed completed successfully!');
  console.log('');
  console.log('📧 Admin user created:');
  console.log('   Email: admin@benefactor.local');
  console.log('   Password: ChangeMe123!');
  console.log('');
  console.log('👥 Demo clients created: 2');
  console.log('🔄 Workflows created: 1');

  await AppDataSource.destroy();
}

seed().catch((error) => {
  console.error('❌ Seed failed:', error);
  process.exit(1);
});
