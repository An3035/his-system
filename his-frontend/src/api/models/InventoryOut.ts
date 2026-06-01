/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DrugOut } from './DrugOut';
export type InventoryOut = {
    id: number;
    drug_id: number;
    stock_qty: string;
    alert_qty: string;
    pharmacy_type: string;
    updated_at: string;
    drug: DrugOut;
};

