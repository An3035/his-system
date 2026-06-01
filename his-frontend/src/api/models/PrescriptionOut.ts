/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PrescriptionItemOut } from './PrescriptionItemOut';
export type PrescriptionOut = {
    id: number;
    pres_no: string;
    registration_id: number;
    pres_type: string;
    total_amount: string;
    payment_status: string;
    dispensed: boolean;
    created_at: string;
    items?: Array<PrescriptionItemOut>;
};

