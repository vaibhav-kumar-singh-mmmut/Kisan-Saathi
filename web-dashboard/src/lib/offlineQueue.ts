import { get, set, del } from 'idb-keyval'

export interface QueuedScan {
  id: string;
  timestamp: number;
  imageSrc: string; // base64 compressed image
  gpsLat?: number;
  gpsLng?: number;
  gpsTimestamp?: number;
  hasMismatchWarning?: boolean;
}

const QUEUE_KEY = 'kisan_saathi_scan_queue';

export async function getQueuedScans(): Promise<QueuedScan[]> {
  try {
    const queue = await get<QueuedScan[]>(QUEUE_KEY);
    return queue || [];
  } catch (error) {
    console.error('Failed to get offline queue:', error);
    return [];
  }
}

export async function saveScanToQueue(scan: Omit<QueuedScan, 'id' | 'timestamp'>): Promise<QueuedScan> {
  const queue = await getQueuedScans();
  
  const newScan: QueuedScan = {
    ...scan,
    id: `scan_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    timestamp: Date.now()
  };

  queue.push(newScan);
  
  try {
    await set(QUEUE_KEY, queue);
    return newScan;
  } catch (error) {
    console.error('Failed to save scan to offline queue:', error);
    throw error;
  }
}

export async function removeScanFromQueue(id: string): Promise<void> {
  const queue = await getQueuedScans();
  const filteredQueue = queue.filter(scan => scan.id !== id);
  
  try {
    await set(QUEUE_KEY, filteredQueue);
  } catch (error) {
    console.error(`Failed to remove scan ${id} from queue:`, error);
    throw error;
  }
}

export async function clearQueue(): Promise<void> {
  try {
    await del(QUEUE_KEY);
  } catch (error) {
    console.error('Failed to clear offline queue:', error);
    throw error;
  }
}
